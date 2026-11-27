#include "Modules/ModuleManager.h"

IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, ChaosIncline, "ChaosIncline");

#if WITH_DEV_AUTOMATION_TESTS

#include "Chaos/Collision/PBDCollisionConstraint.h"
#include "Chaos/PBDCollisionConstraints.h"
#include "Chaos/PBDRigidsEvolutionGBF.h"
#include "Chaos/SimCallbackObject.h"
#include "Components/BoxComponent.h"
#include "CoreGlobals.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "PBDRigidsSolver.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "Physics/Experimental/PhysScene_Chaos.h"
#include "PhysicsProxy/SingleParticlePhysicsProxy.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FChaosInclineTest, "DexLab.ChaosIncline",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
struct FContact
{
    double Distance;
    FVector Impulse;
    FVector PushOut;
    double StaticFriction;
    double DynamicFriction;
};

struct FInclineSample : Chaos::FSimCallbackOutput
{
    bool bHasBody = false;
    double Start = 0;
    double Dt = 0;
    FVector Gravity;
    FVector Position;
    FQuat Rotation;
    FVector Velocity;
    FVector Angular;
    TArray<FContact> Contacts;

    void Reset()
    {
        bHasBody = false;
        Contacts.Reset();
    }
};

class FReadInclineContacts final : public Chaos::TSimCallbackObject<
    Chaos::FSimCallbackNoInput, FInclineSample, Chaos::ESimCallbackOptions::PostSolve>
{
public:
    explicit FReadInclineContacts(const Chaos::FSingleParticlePhysicsProxy* InBody) : Body(InBody) {}

private:
    void OnPreSimulate_Internal() override {}

    void OnPostSolve_Internal() override
    {
        const auto* Handle = Body->GetHandle_LowLevel();
        if (!Handle)
        {
            return;
        }
        const auto* Particle = Handle->CastToRigidParticle();
        if (!Particle)
        {
            return;
        }
        const auto* Solver = static_cast<const Chaos::FPBDRigidsSolver*>(GetSolver());
        const auto* Evolution = Solver->GetEvolution();
        FInclineSample& Sample = GetProducerOutputData_Internal();
        Sample.bHasBody = true;
        Sample.Start = GetSimTime_Internal();
        Sample.Dt = GetDeltaTime_Internal();
        Sample.Gravity = FVector(Evolution->GetGravityForces().GetAcceleration(0)) / 100.0;
        // Here X/R still refer to the opening pose. P/Q are the solved closing pose.
        Sample.Position = FVector(Particle->GetP()) / 100.0;
        Sample.Rotation = FQuat(Particle->GetQ());
        Sample.Velocity = FVector(Particle->V()) / 100.0;
        Sample.Angular = FVector(Particle->W());
        for (const auto* Constraint : Evolution->GetCollisionConstraints().GetConstraints())
        {
            if (!Constraint->IsEnabled() || Constraint->GetIsProbe())
            {
                continue;
            }
            const bool bFirst = Constraint->GetParticle0() == Handle;
            const bool bSecond = Constraint->GetParticle1() == Handle;
            if (!bFirst && !bSecond)
            {
                continue;
            }
            const double Scale = bFirst ? 0.01 : -0.01;
            for (int32 Index = 0; Index < Constraint->NumManifoldPoints(); ++Index)
            {
                const auto& Point = Constraint->GetManifoldPoint(Index);
                const auto& Result = Constraint->GetManifoldPointResult(Index);
                if (Result.bIsValid && !Point.Flags.bDisabled)
                {
                    Sample.Contacts.Add({Point.ContactPoint.Phi / 100.0,
                        FVector(Result.NetImpulse) * Scale, FVector(Result.NetPushOut) * Scale,
                        Constraint->GetStaticFriction(), Constraint->GetDynamicFriction()});
                }
            }
        }
    }

    const Chaos::FSingleParticlePhysicsProxy* Body;
};

FString StateRow(int32 Step, double Start, double Dt, const FVector& Position,
    const FQuat& Rotation, const FVector& Velocity, const FVector& Angular)
{
    return FString::Printf(TEXT("%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n"),
        Step, Start, Dt, Position.X, Position.Y, Position.Z, Rotation.W, Rotation.X,
        Rotation.Y, Rotation.Z, Velocity.X, Velocity.Y, Velocity.Z, Angular.X, Angular.Y, Angular.Z);
}

class FRunChaosIncline final : public IAutomationLatentCommand
{
public:
    FRunChaosIncline(FAutomationTestBase* InTest, TSharedPtr<FJsonObject> InProtocol,
        TArray<TSharedPtr<FJsonValue>> InCases, FString InOutput)
        : Test(InTest), Protocol(MoveTemp(InProtocol)), Cases(MoveTemp(InCases)), Output(MoveTemp(InOutput)) {}

    bool Update() override
    {
        if (LastFrame == GFrameCounter)
        {
            return false;
        }
        LastFrame = GFrameCounter;
        if (World == nullptr)
        {
            StartCase(*Cases[CaseIndex]->AsObject());
        }
        World->Tick(LEVELTICK_All, static_cast<float>(TimeStep));
        ++Step;
        {
            auto Sample = Reader->PopFutureOutputData_External();
            if (!Sample || !Sample->bHasBody)
            {
                Test->AddError(FString::Printf(TEXT("%s step %d missing post-solve record"), *CaseId, Step));
                FinishCase();
                return true;
            }
            States += StateRow(Step, Sample->Start, Sample->Dt, Sample->Position, Sample->Rotation,
                Sample->Velocity, Sample->Angular);
            Gravity = Sample->Gravity;
            for (const FContact& Point : Sample->Contacts)
            {
                Contacts += FString::Printf(TEXT("%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n"),
                    Step, Point.Distance, Point.Impulse.X, Point.Impulse.Y, Point.Impulse.Z,
                    Point.PushOut.X, Point.PushOut.Y, Point.PushOut.Z, Point.StaticFriction, Point.DynamicFriction);
            }
        }
        if (Reader->PopFutureOutputData_External())
        {
            Test->AddError(TEXT("A manual world tick yielded multiple solver outputs"));
            FinishCase();
            return true;
        }
        if (Step < NumSteps)
        {
            return false;
        }
        FinishCase();
        return ++CaseIndex == Cases.Num();
    }

private:
    UBoxComponent* AddBox(const FVector& Position, const FQuat& Rotation, const FVector& Extent,
        UPhysicalMaterial* Material, bool bSimulate, bool bCollision)
    {
        AActor* Actor = World->SpawnActor<AActor>(Position, Rotation.Rotator());
        auto* Shape = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Shape);
        Shape->SetWorldTransform(FTransform(Rotation, Position));
        Shape->InitBoxExtent(Extent);
        Shape->SetMobility(bSimulate ? EComponentMobility::Movable : EComponentMobility::Static);
        Shape->SetCollisionObjectType(bSimulate ? ECC_PhysicsBody : ECC_WorldStatic);
        Shape->SetCollisionResponseToAllChannels(ECR_Block);
        Shape->SetCollisionEnabled(bCollision ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
        Shape->SetPhysMaterialOverride(Material);
        Shape->SetLinearDamping(0.0f);
        Shape->SetAngularDamping(0.0f);
        if (bSimulate)
        {
            Shape->SetMassOverrideInKg(NAME_None, Protocol->GetNumberField(TEXT("mass_kg")), true);
            Shape->SetSimulatePhysics(true);
        }
        Shape->RegisterComponent();
        return Shape;
    }

    void StartCase(const FJsonObject& Case)
    {
        CaseId = Case.GetStringField(TEXT("id"));
        TimeStep = Case.GetNumberField(TEXT("timestep"));
        NumSteps = FMath::RoundToInt(Protocol->GetNumberField(TEXT("duration_s")) / TimeStep);
        Step = 0;
        World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true,
            ERHIFeatureLevel::Num, &Init);
        GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        World->GetWorldSettings()->bGlobalGravitySet = true;
        World->GetWorldSettings()->GlobalGravityZ = -100.0 * Protocol->GetNumberField(TEXT("gravity_m_s2"));

        const float Mu = Case.GetNumberField(TEXT("friction"));
        auto* Material = NewObject<UPhysicalMaterial>(World);
        Material->Friction = Mu;
        Material->StaticFriction = Mu;
        Material->Restitution = 0.0f;
        Material->bOverrideFrictionCombineMode = true;
        Material->FrictionCombineMode = EFrictionCombineMode::Average;
        const FQuat Rotation(FVector::YAxisVector,
            FMath::DegreesToRadians(Case.GetNumberField(TEXT("angle_deg"))));
        const FVector Normal = Rotation.RotateVector(FVector::UpVector);
        const double Half = 50.0 * Protocol->GetNumberField(TEXT("side_m"));
        bool bNoFloor = false;
        Case.TryGetBoolField(TEXT("negative_no_floor"), bNoFloor);
        // The center and surface plane are independent of the finite slab thickness.
        const auto* Floor = AddBox(-10.0 * Normal, Rotation, FVector(2000, 2000, 10), Material, false, !bNoFloor);
        auto* Box = AddBox(Half * Normal, Rotation, FVector(Half), Material, true, true);
        World->InitializeActorsForPlay(FURL());
        World->BeginPlay();

        Mass = Box->GetMass();
        Inertia = Box->GetInertiaTensor() / 10000.0;
        FloorNormal = Floor->GetUpVector();
        const FVector FloorPoint = Floor->GetComponentLocation() + 10.0 * FloorNormal;
        FloorHeight = FloorPoint.Dot(FloorNormal) / 100.0;
        BoxSide = Box->GetScaledBoxExtent() / 50.0;
        States = TEXT("step,start_s,dt_s,x_m,y_m,z_m,qw,qx,qy,qz,vx_m_s,vy_m_s,vz_m_s,wx_rad_s,wy_rad_s,wz_rad_s\n");
        States += StateRow(0, 0.0, 0.0, Box->GetComponentLocation() / 100.0,
            Box->GetComponentQuat(), Box->GetPhysicsLinearVelocity() / 100.0,
            Box->GetPhysicsAngularVelocityInRadians());
        Contacts = TEXT("step,distance_m,jx_ns,jy_ns,jz_ns,px_kg_m,py_kg_m,pz_kg_m,mu_static,mu_dynamic\n");
        Test->TestFalse(TEXT("Physics uses synchronized steps"), World->GetPhysicsScene()->GetSolver()->IsUsingAsyncResults());
        Reader = World->GetPhysicsScene()->GetSolver()->CreateAndRegisterSimCallbackObject_External<
            FReadInclineContacts>(Box->GetBodyInstance()->GetPhysicsActor());
    }

    void FinishCase()
    {
        const FString Directory = FPaths::Combine(Output, CaseId);
        IFileManager::Get().MakeDirectory(*Directory, true);
        Test->TestTrue(TEXT("Saved states"), FFileHelper::SaveStringToFile(States, *FPaths::Combine(Directory, TEXT("states.csv"))));
        Test->TestTrue(TEXT("Saved contacts"), FFileHelper::SaveStringToFile(Contacts, *FPaths::Combine(Directory, TEXT("contacts.csv"))));
        const FString Readback = FString::Printf(
            TEXT("{\"mass_kg\":%.17g,\"inertia_kg_m2\":[%.17g,%.17g,%.17g],\"gravity_m_s2\":[%.17g,%.17g,%.17g],\"floor_height_m\":%.17g,\"floor_normal\":[%.17g,%.17g,%.17g],\"box_side_m\":[%.17g,%.17g,%.17g],\"completed_steps\":%d}\n"),
            Mass, Inertia.X, Inertia.Y, Inertia.Z, Gravity.X, Gravity.Y, Gravity.Z, FloorHeight,
            FloorNormal.X, FloorNormal.Y, FloorNormal.Z, BoxSide.X, BoxSide.Y, BoxSide.Z, Step);
        Test->TestTrue(TEXT("Saved native readback"), FFileHelper::SaveStringToFile(Readback, *FPaths::Combine(Directory, TEXT("readback.json"))));
        World->GetPhysicsScene()->GetSolver()->UnregisterAndFreeSimCallbackObject_External(Reader);
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        World = nullptr;
    }

    const UWorld::InitializationValues Init = UWorld::InitializationValues()
        .CreatePhysicsScene(true).ShouldSimulatePhysics(true)
        .CreateNavigation(false).CreateAISystem(false).AllowAudioPlayback(false);
    FAutomationTestBase* Test;
    TSharedPtr<FJsonObject> Protocol;
    TArray<TSharedPtr<FJsonValue>> Cases;
    FString Output;
    FString CaseId;
    FString States;
    FString Contacts;
    UWorld* World = nullptr;
    FReadInclineContacts* Reader = nullptr;
    uint64 LastFrame = 0;
    int32 CaseIndex = 0;
    int32 Step = 0;
    int32 NumSteps = 0;
    double TimeStep = 0.0;
    double Mass = 0.0;
    double FloorHeight = 0.0;
    FVector Inertia = FVector::ZeroVector;
    FVector Gravity = FVector::ZeroVector;
    FVector FloorNormal = FVector::ZeroVector;
    FVector BoxSide = FVector::ZeroVector;
};
}

bool FChaosInclineTest::RunTest(const FString& Parameters)
{
    FString ManifestPath, Output, Text;
    double OnlyStep = 0.0;
    if (!FParse::Value(FCommandLine::Get(), TEXT("DexInclineManifest="), ManifestPath) ||
        !FParse::Value(FCommandLine::Get(), TEXT("DexInclineOutput="), Output) ||
        !FFileHelper::LoadFileToString(Text, *ManifestPath) ||
        IFileManager::Get().DirectoryExists(*Output))
    {
        AddError(TEXT("Supply an existing DexInclineManifest and a fresh DexInclineOutput directory"));
        return false;
    }
    FParse::Value(FCommandLine::Get(), TEXT("DexInclineStep="), OnlyStep);
    TSharedPtr<FJsonObject> Protocol;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Protocol))
    {
        AddError(TEXT("Invalid incline manifest"));
        return false;
    }
    TArray<TSharedPtr<FJsonValue>> Cases;
    for (const auto& Case : Protocol->GetArrayField(TEXT("cases")))
    {
        if (OnlyStep == 0.0 || FMath::IsNearlyEqual(Case->AsObject()->GetNumberField(TEXT("timestep")), OnlyStep, 1e-12))
        {
            Cases.Add(Case);
        }
    }
    if (Cases.IsEmpty())
    {
        AddError(TEXT("No cases selected"));
        return false;
    }
    IConsoleManager::Get().FindConsoleVariable(TEXT("p.Chaos.Solver.Sleep.Enabled"))->Set(false, ECVF_SetByCode);
    ADD_LATENT_AUTOMATION_COMMAND(FRunChaosIncline(this, Protocol, MoveTemp(Cases), Output));
    return true;
}
#endif
