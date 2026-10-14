// Standalone official PhysX observations. No state writes after initialization.
#include "PxPhysicsAPI.h"
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace physx;

static void quoted(std::ostream& out, const std::string& text) {
    out << '"';
    for (unsigned char c : text) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c) << std::dec;
        else out << c;
    }
    out << '"';
}
static void vec(std::ostream& out, const PxVec3& x) { out << '[' << x.x << ',' << x.y << ',' << x.z << ']'; }
static void pose(std::ostream& out, const PxTransform& x) {
    out << '[' << x.p.x << ',' << x.p.y << ',' << x.p.z << ',' << x.q.w << ',' << x.q.x << ',' << x.q.y << ',' << x.q.z << ']';
}
static void state(std::ostream& out, const PxRigidDynamic& body, double time) {
    const auto p = body.getGlobalPose(); const auto v = body.getLinearVelocity(); const auto w = body.getAngularVelocity();
    out << '[' << time << ',' << p.p.x << ',' << p.p.y << ',' << p.p.z << ',' << p.q.w << ',' << p.q.x << ',' << p.q.y << ',' << p.q.z
        << ',' << v.x << ',' << v.y << ',' << v.z << ',' << w.x << ',' << w.y << ',' << w.z << ']';
}
struct Errors : PxErrorCallback {
    std::vector<std::string> messages;
    void reportError(PxErrorCode::Enum code, const char* message, const char* file, int line) override {
        std::string name(file ? file : ""); const auto slash = name.find_last_of("/\\");
        if (slash != std::string::npos) name = name.substr(slash + 1);
        messages.push_back(std::to_string(int(code)) + ": " + message + " (" + name + ":" + std::to_string(line) + ")");
    }
    void write(std::ostream& out) const {
        out << '['; for (size_t i=0; i<messages.size(); ++i) { if(i) out << ','; quoted(out,messages[i]); } out << ']';
    }
};
struct Pair {
    bool cube_first;
    bool normal_impulses_available, friction_impulses_available;
    unsigned flags, patches, declared_contacts;
    std::vector<PxContactPairPoint> contacts;
    std::vector<PxContactPairFrictionAnchor> anchors;
};
struct Contacts : PxSimulationEventCallback {
    PxRigidDynamic* cube = nullptr;
    PxRigidStatic* plane = nullptr;
    std::vector<Pair> pairs;
    bool overflow = false;
    static constexpr unsigned capacity = 256;
    void onContact(const PxContactPairHeader& header, const PxContactPair* input, PxU32 count) override {
        for (unsigned i=0; i<count; ++i) {
            const auto& p = input[i];
            if (!((header.actors[0] == cube && header.actors[1] == plane) ||
                  (header.actors[0] == plane && header.actors[1] == cube))) { overflow = true; continue; }
            Pair row{header.actors[0] == cube, p.contactImpulses != nullptr, p.frictionPatches != nullptr,
                     unsigned(p.flags), p.patchCount, p.contactCount, {}, {}};
            row.contacts.resize(capacity); row.anchors.resize(capacity);
            const unsigned nc = p.extractContacts(row.contacts.data(), capacity);
            const unsigned na = p.extractFrictionAnchors(row.anchors.data(), capacity);
            // The known plane/box fixture has at most four points/two anchors;
            // equality to capacity is conservatively rejected, never truncated.
            if (nc != p.contactCount || nc >= capacity || na >= capacity) overflow = true;
            row.contacts.resize(nc); row.anchors.resize(na); pairs.push_back(std::move(row));
        }
    }
    void onConstraintBreak(PxConstraintInfo*, PxU32) override { overflow = true; }
    void onWake(PxActor**, PxU32) override {}
    void onSleep(PxActor**, PxU32) override {}
    void onTrigger(PxTriggerPair*, PxU32) override { overflow = true; }
    void onAdvance(const PxRigidBody* const*, const PxTransform*, const PxU32) override {}
    void write(std::ostream& out) const {
        out << '[';
        for(size_t i=0;i<pairs.size();++i) {
            if(i) out << ',';
            const auto& p=pairs[i];
            out << "{\"cube_first\":" << (p.cube_first ? "true":"false") << ",\"flags\":" << p.flags
                << ",\"normal_impulses_available\":" << (p.normal_impulses_available ? "true":"false")
                << ",\"friction_impulses_available\":" << (p.friction_impulses_available ? "true":"false")
                << ",\"patch_count\":" << p.patches << ",\"declared_contacts\":" << p.declared_contacts << ",\"contacts\":[";
            for(size_t j=0;j<p.contacts.size();++j) {
                if(j) out << ',';
                const auto& c=p.contacts[j];
                out << "{\"position\":"; vec(out,c.position); out << ",\"normal\":"; vec(out,c.normal);
                out << ",\"separation\":" << c.separation << ",\"impulse\":"; vec(out,c.impulse); out << '}';
            }
            out << "],\"friction_anchors\":[";
            for(size_t j=0;j<p.anchors.size();++j) {
                if(j) out << ',';
                const auto& a=p.anchors[j];
                out << "{\"position\":"; vec(out,a.position); out << ",\"impulse\":"; vec(out,a.impulse); out << '}';
            }
            out << "]}";
        }
        out << ']';
    }
};
static PxFilterFlags filter(PxFilterObjectAttributes, PxFilterData, PxFilterObjectAttributes, PxFilterData,
                            PxPairFlags& flags, const void*, PxU32) {
    flags = PxPairFlag::eSOLVE_CONTACT | PxPairFlag::eDETECT_DISCRETE_CONTACT
          | PxPairFlag::eNOTIFY_TOUCH_FOUND | PxPairFlag::eNOTIFY_TOUCH_PERSISTS | PxPairFlag::eNOTIFY_CONTACT_POINTS;
    return PxFilterFlag::eDEFAULT;
}
static void shape(std::ostream& out, const PxShape& s) {
    out << "{\"geometry_type\":" << int(s.getGeometry().getType()) << ",\"flags\":" << unsigned(s.getFlags())
        << ",\"contact_offset\":" << s.getContactOffset() << ",\"rest_offset\":" << s.getRestOffset()
        << ",\"local_pose\":"; pose(out,s.getLocalPose());
    if(s.getGeometry().getType()==PxGeometryType::eBOX) { out << ",\"half_extents\":"; vec(out,static_cast<const PxBoxGeometry&>(s.getGeometry()).halfExtents); }
    out << '}';
}
int main(int argc, char** argv) {
    // One process owns exactly one case. Independent invocations prevent reset contamination.
    if(argc != 8) { std::cerr << "profile angle_deg friction timestep steps negative reverse_order\n"; return 2; }
    try {
        const std::string profile(argv[1]);
        const bool tgs=profile=="tgs" || profile=="tgs-external", every=profile=="pgs-friction";
        if(!tgs && !every && profile!="pgs") throw std::invalid_argument("Unknown profile");
        const double angle=std::stod(argv[2])*std::acos(-1.)/180., mu=std::stod(argv[3]), requested_dt=std::stod(argv[4]);
        const int steps=std::stoi(argv[5]); const bool negative=std::stoi(argv[6])!=0, reverse=std::stoi(argv[7])!=0;
        if(!std::isfinite(angle) || !std::isfinite(mu) || !std::isfinite(requested_dt) || mu<0 || mu>1 || requested_dt<=0 || requested_dt>.01 || steps<0 || steps>4000)
            throw std::invalid_argument("Invalid bounded case");
        const PxReal dt=PxReal(requested_dt); const double h=double(dt);
        PxDefaultAllocator allocator; Errors errors; Contacts contacts;
        PxFoundation* foundation=PxCreateFoundation(PX_PHYSICS_VERSION,allocator,errors);
        if(!foundation) throw std::runtime_error("Foundation rejected SDK version");
        PxPhysics* physics=PxCreatePhysics(PX_PHYSICS_VERSION,*foundation,PxTolerancesScale(),false,nullptr);
        if(!physics) throw std::runtime_error("Physics rejected SDK version");
        PxDefaultCpuDispatcher* dispatcher=PxDefaultCpuDispatcherCreate(1);
        PxSceneDesc desc(physics->getTolerancesScale()); desc.gravity=PxVec3(0,0,-9.81f);
        desc.cpuDispatcher=dispatcher; desc.filterShader=filter; desc.simulationEventCallback=&contacts;
        desc.solverType=tgs?PxSolverType::eTGS:PxSolverType::ePGS;
        desc.flags |= PxSceneFlag::eENABLE_ENHANCED_DETERMINISM;
        if(every) desc.flags |= PxSceneFlag::eENABLE_FRICTION_EVERY_ITERATION;
        if(profile=="tgs-external") desc.flags |= PxSceneFlag::eENABLE_EXTERNAL_FORCES_EVERY_ITERATION_TGS;
        if(!desc.isValid()) throw std::runtime_error("Native scene descriptor rejected");
        PxScene* scene=physics->createScene(desc); if(!scene) throw std::runtime_error("Native scene creation failed");
        PxMaterial* material=physics->createMaterial(PxReal(mu),PxReal(mu),0);
        material->setFrictionCombineMode(PxCombineMode::eAVERAGE); material->setRestitutionCombineMode(PxCombineMode::eAVERAGE);
        const PxVec3 normal(PxReal(std::sin(angle)),0,PxReal(std::cos(angle)));
        PxRigidStatic* plane=PxCreatePlane(*physics,PxPlane(normal,0),*material);
        PxRigidDynamic* cube=physics->createRigidDynamic(PxTransform(normal*.02f,PxQuat(PxReal(angle),PxVec3(0,1,0))));
        PxShape* cube_shape=physics->createShape(PxBoxGeometry(.02f,.02f,.02f),*material,true);
        cube->attachShape(*cube_shape); cube_shape->release();
        PxShape* plane_shape=nullptr; plane->getShapes(&plane_shape,1);
        cube_shape->setContactOffset(.0001f); plane_shape->setContactOffset(.0001f);
        cube_shape->setRestOffset(0); plane_shape->setRestOffset(0);
        PxRigidBodyExt::updateMassAndInertia(*cube,1000.f);
        // The helper ignores non-simulation shapes. Freeze the same mass first,
        // then disable only contact generation for the negative control.
        if(negative) cube_shape->setFlag(PxShapeFlag::eSIMULATION_SHAPE,false);
        cube->setLinearDamping(0); cube->setAngularDamping(0);
        cube->setSleepThreshold(0); cube->setStabilizationThreshold(0);
        cube->setSolverIterationCounts(8,2); contacts.cube=cube; contacts.plane=plane;
        if(reverse) { scene->addActor(*cube); scene->addActor(*plane); } else { scene->addActor(*plane); scene->addActor(*cube); }
        std::cout << std::setprecision(17);
        PxU32 position_iterations=0,velocity_iterations=0; cube->getSolverIterationCounts(position_iterations,velocity_iterations);
        std::cout << "{\"kind\":\"admission\",\"sdk_version\":\"5.9.0\",\"sdk_version_integer\":" << PX_PHYSICS_VERSION
                  << ",\"real_bytes\":" << sizeof(PxReal) << ",\"profile\":"; quoted(std::cout,profile);
        std::cout << ",\"requested_timestep\":" << requested_dt << ",\"effective_timestep\":" << h
                  << ",\"solver_type\":" << int(scene->getSolverType()) << ",\"scene_flags\":" << unsigned(scene->getFlags())
                  << ",\"friction_type\":" << int(scene->getFrictionType()) << ",\"gravity\":"; vec(std::cout,scene->getGravity());
        std::cout << ",\"position_iterations\":" << position_iterations << ",\"velocity_iterations\":" << velocity_iterations
                  << ",\"dynamic_actors\":" << scene->getNbActors(PxActorTypeFlag::eRIGID_DYNAMIC)
                  << ",\"static_actors\":" << scene->getNbActors(PxActorTypeFlag::eRIGID_STATIC)
                  << ",\"cpu_worker_count\":" << dispatcher->getWorkerCount() << ",\"contact_capacity\":" << Contacts::capacity
                  << ",\"contact_report_bytes\":" << scene->getContactReportStreamBufferSize()
                  << ",\"friction_offset_threshold\":" << scene->getFrictionOffsetThreshold()
                  << ",\"friction_correlation_distance\":" << scene->getFrictionCorrelationDistance()
                  << ",\"bounce_threshold_velocity\":" << scene->getBounceThresholdVelocity()
                  << ",\"mass\":" << cube->getMass() << ",\"inertia\":"; vec(std::cout,cube->getMassSpaceInertiaTensor());
        std::cout << ",\"mass_frame\":"; pose(std::cout,cube->getCMassLocalPose());
        std::cout << ",\"plane_pose\":"; pose(std::cout,plane->getGlobalPose());
        std::cout << ",\"cube_shape\":"; shape(std::cout,*cube_shape); std::cout << ",\"plane_shape\":"; shape(std::cout,*plane_shape);
        std::cout << ",\"linear_damping\":" << cube->getLinearDamping() << ",\"angular_damping\":" << cube->getAngularDamping()
                  << ",\"sleep_threshold\":" << cube->getSleepThreshold() << ",\"stabilization_threshold\":" << cube->getStabilizationThreshold()
                  << ",\"body_flags\":" << unsigned(cube->getRigidBodyFlags()) << ",\"actor_flags\":" << unsigned(cube->getActorFlags())
                  << ",\"max_linear_velocity\":" << cube->getMaxLinearVelocity() << ",\"max_angular_velocity\":" << cube->getMaxAngularVelocity()
                  << ",\"max_depenetration_velocity\":" << cube->getMaxDepenetrationVelocity()
                  << ",\"static_friction\":" << material->getStaticFriction() << ",\"dynamic_friction\":" << material->getDynamicFriction()
                  << ",\"restitution\":" << material->getRestitution() << ",\"friction_combine_mode\":" << int(material->getFrictionCombineMode())
                  << ",\"material_flags\":" << unsigned(material->getFlags()) << ",\"scene_timestamp\":" << scene->getTimestamp()
                  << ",\"initial_state\":"; state(std::cout,*cube,0); std::cout << ",\"errors\":"; errors.write(std::cout); std::cout << "}\n";
        double native_seconds=0;
        for(int step=0;step<steps;++step) {
            contacts.pairs.clear(); contacts.overflow=false;
            std::ostringstream before; before << std::setprecision(17); state(before,*cube,step*h);
            const auto begin=std::chrono::steady_clock::now(); scene->simulate(dt); const bool fetched=scene->fetchResults(true);
            const double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count(); native_seconds+=elapsed;
            if(!fetched) throw std::runtime_error("Native results unavailable");
            std::cout << "{\"kind\":\"step\",\"step\":" << step << ",\"scene_timestamp\":" << scene->getTimestamp()
                      << ",\"interval_start_s\":" << step*h << ",\"interval_end_s\":" << (step+1)*h << ",\"pre_state\":" << before.str()
                      << ",\"state\":"; state(std::cout,*cube,(step+1)*h);
            std::cout << ",\"sleeping\":" << (cube->isSleeping()?"true":"false") << ",\"overflow\":" << (contacts.overflow?"true":"false")
                      << ",\"pairs\":"; contacts.write(std::cout);
            std::cout << ",\"native_step_wall_s\":" << elapsed << ",\"errors\":"; errors.write(std::cout); std::cout << "}\n";
        }
        const bool failed=!errors.messages.empty();
        std::cout << "{\"kind\":\"completion\",\"completed_steps\":" << steps << ",\"state_writes_after_initialization\":0,\"native_step_wall_s\":"
                  << native_seconds << ",\"errors\":"; errors.write(std::cout); std::cout << "}\n";
        cube->release(); plane->release(); scene->release(); material->release(); dispatcher->release(); physics->release(); foundation->release();
        return failed?1:0;
    } catch(const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
