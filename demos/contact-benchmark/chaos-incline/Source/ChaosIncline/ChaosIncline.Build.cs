using UnrealBuildTool;

public class ChaosIncline : ModuleRules
{
    public ChaosIncline(ReadOnlyTargetRules target) : base(target)
    {
        PrivateDependencyModuleNames.AddRange(
            new[] { "Core", "CoreUObject", "Engine", "PhysicsCore", "Chaos", "Json" }
        );
    }
}
