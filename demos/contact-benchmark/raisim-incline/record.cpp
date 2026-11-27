#include <raisim/World.hpp>
#include <nlohmann/json.hpp>

#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numbers>
#include <stdexcept>

namespace {
using Json = nlohmann::json;
namespace fs = std::filesystem;

constexpr double slab_thickness = 0.2;
constexpr double slab_extent = 40.0;

std::ofstream open_output(const fs::path& path) {
    std::ofstream stream;
    stream.exceptions(std::ofstream::failbit | std::ofstream::badbit);
    stream.open(path);
    stream << std::setprecision(17);
    return stream;
}

template <class Derived>
void csv_vector(std::ostream& stream, const Eigen::MatrixBase<Derived>& vector) {
    for (Eigen::Index i = 0; i < vector.size(); ++i) {
        stream << ',' << vector(i);
    }
}

template <class Derived>
Json array(const Eigen::MatrixBase<Derived>& vector) {
    Json values = Json::array();
    for (Eigen::Index i = 0; i < vector.size(); ++i) {
        values.push_back(vector(i));
    }
    return values;
}

void state_row(std::ostream& stream, const raisim::Box& box, int step,
               double start, double duration) {
    stream << step << ',' << start << ',' << duration;
    csv_vector(stream, box.getPosition());
    csv_vector(stream, box.getQuaternion());
    csv_vector(stream, box.getLinearVelocity());
    csv_vector(stream, box.getAngularVelocity());
    stream << '\n';
}

void record_case(const Json& protocol, const Json& condition, const fs::path& output) {
    const std::string case_id = condition.at("id");
    if (case_id.empty() || case_id == "." || case_id == ".." || fs::path(case_id).filename() != case_id) {
        throw std::runtime_error("Invalid case id");
    }
    const auto directory = output / case_id;
    if (!fs::create_directory(directory)) {
        throw std::runtime_error("Case output already exists: " + case_id);
    }

    const double step_size = condition.at("timestep");
    const double mass = protocol.at("mass_kg");
    const double side = protocol.at("side_m");
    const double gravity = protocol.at("gravity_m_s2");
    const double duration = protocol.at("duration_s");
    const double friction = condition.at("friction");
    const double angle = condition.at("angle_deg").get<double>() * std::numbers::pi / 180;
    const Eigen::Quaterniond orientation(Eigen::AngleAxisd(angle, Eigen::Vector3d::UnitY()));
    const Eigen::Vector3d normal = orientation * Eigen::Vector3d::UnitZ();

    raisim::World world;
    world.setTimeStep(step_size);
    world.setGravity({0, 0, -gravity});
    world.setSleepingEnabled(false);
    world.setMaterialPairProp("cube", "slab", friction, 0.0, 0.0, friction, 0.001);
    raisim::Box* floor = nullptr;
    if (!condition.value("negative_no_floor", false)) {
        floor = world.addBox(slab_extent, slab_extent, slab_thickness, 1.0, "slab");
        floor->setBodyType(raisim::BodyType::STATIC);
        floor->setOrientation(orientation);
        floor->setPosition(Eigen::Vector3d(-slab_thickness / 2 * normal));
    }
    raisim::Box* box = world.addBox(side, side, side, mass, "cube");
    box->setOrientation(orientation);
    box->setPosition(Eigen::Vector3d(side / 2 * normal));
    box->setLinearDamping(0.0);
    box->setAngularDamping({0, 0, 0});

    auto& solver = world.getContactSolver();
    const auto& settings = solver.getConfig();
    const auto& pair = world.getMaterialPairProperties("cube", "slab");
    Json readback = {
        {"version", DEXLAB_RAISIM_VERSION},
        {"mass_kg", box->getMass()},
        {"inertia_kg_m2", array(box->getInertiaMatrix_B().diagonal())},
        {"gravity_m_s2", array(world.getGravity().e())},
        {"box_side_m", array(box->getDim().e())},
        {"floor_size_m", floor ? array(floor->getDim().e()) : Json(nullptr)},
        {"floor_center_m", floor ? array(floor->getPosition()) : Json(nullptr)},
        {"floor_quaternion_wxyz", floor ? array(floor->getQuaternion()) : Json(nullptr)},
        {"material_pair", {
            {"static_friction", pair.c_static_f}, {"dynamic_friction", pair.c_f},
            {"restitution", pair.c_r}, {"static_transition_speed_m_s", pair.v_static_speed},
            {"rolling_friction", pair.c_rolling_f}, {"spinning_friction", pair.c_spinning_f},
        }},
        {"solver", {
            {"max_iterations", settings.maxIteration}, {"row_tolerance", settings.error_to_terminate},
            {"erp", settings.erp}, {"erp2", settings.erp2},
        }},
        {"timestep_s", world.getTimeStep()},
        {"sleeping_enabled", world.getSleepingParameters().enabled},
        {"force_epoch", "Last completed native step, impulse in contact frame acting on object A"},
    };

    auto states = open_output(directory / "states.csv");
    auto contacts = open_output(directory / "contacts.csv");
    auto solver_steps = open_output(directory / "solver.csv");
    states << "step,start_s,dt_s,x_m,y_m,z_m,qw,qx,qy,qz,vx_m_s,vy_m_s,vz_m_s,wx_rad_s,wy_rad_s,wz_rad_s\n";
    contacts << "step,distance_m,box_is_a,local_jx_ns,local_jy_ns,local_jz_ns,"
                "f00,f01,f02,f10,f11,f12,f20,f21,f22,px_m,py_m,pz_m\n";
    solver_steps << "step,iterations,stalled\n";
    state_row(states, *box, 0, 0, 0);
    const int steps = std::lround(duration / step_size);
    for (int step = 1; step <= steps; ++step) {
        const double start = world.getWorldTime();
        world.integrate();
        state_row(states, *box, step, start, world.getWorldTime() - start);
        solver_steps << step << ',' << solver.getLoopCounter() << ',' << solver.isStalled() << '\n';
        for (const auto& contact : box->getContacts()) {
            if (!floor || contact.skip() || !contact.getImpulsePtr() ||
                contact.getPairObjectIndex() != floor->getIndexInWorld()) {
                throw std::runtime_error("Unexpected cube contact in " + case_id);
            }
            contacts << step << ',' << contact.getDepth() << ',' << contact.isObjectA();
            csv_vector(contacts, contact.getImpulse().e());
            const auto frame = contact.getContactFrame().e();
            for (int row = 0; row < 3; ++row) {
                csv_vector(contacts, frame.row(row));
            }
            csv_vector(contacts, contact.getPosition().e());
            contacts << '\n';
        }
    }
    states.close();
    contacts.close();
    solver_steps.close();
    readback["completed_steps"] = steps;
    open_output(directory / "readback.json") << readback.dump(2) << '\n';
    std::cout << case_id << ": " << steps << " steps\n";
}
}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 3 && argc != 4) {
            throw std::runtime_error("Usage: record_raisim_incline MANIFEST OUTPUT [TIMESTEP_SECONDS]");
        }
        std::ifstream manifest(argv[1]);
        const Json protocol = Json::parse(manifest);
        if (protocol.value("raisim_version", "2.16.0") != DEXLAB_RAISIM_VERSION) {
            throw std::runtime_error("RaiSim SDK version differs from the manifest");
        }
        const fs::path output(argv[2]);
        if (!fs::create_directory(output)) {
            throw std::runtime_error("Output already exists");
        }
        const double selected_step = argc == 4 ? std::stod(argv[3]) : 0.0;
        if (const char* activation_path = std::getenv("RAISIM_ACTIVATION_FILE")) {
            raisim::World::setActivationKey(activation_path);
        }
        int recorded = 0;
        for (const auto& condition : protocol.at("cases")) {
            if (selected_step == 0 || condition.at("timestep").get<double>() == selected_step) {
                record_case(protocol, condition, output);
                ++recorded;
            }
        }
        if (recorded == 0) {
            throw std::runtime_error("No cases matched the selected timestep");
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
