#include <Eigen/Core>
#include <Eigen/LU>

#include "args.hxx"

#include <fstream>
#include <iostream>

using ChartType = Eigen::Matrix<double, 24, 3>;
using ChartHmType = Eigen::Matrix<double, 24, 4>;
using CCMType = Eigen::Matrix<double, 4, 3>;


std::vector<std::string> StringSplit(const std::string &str, char sep) {
    std::vector<std::string> v;
    std::stringstream ss(str);
    std::string buffer;
    while( std::getline(ss, buffer, sep) ) {
        v.push_back(buffer);
    }
    return v;
}


bool LoadColorchartCsv(const std::string& filename, ChartType& dst_chart) {
    std::ifstream ifs(filename);
    if (!ifs) {
        std::cout << "Can't open " << filename << std::endl;
        return false;
    }

    std::string str;
    std::getline(ifs, str); // skip first line

    int i = 0;
    while (std::getline(ifs, str)) {
        std::vector<std::string> data_str = StringSplit(str, ',');
        dst_chart(i, 0) = std::stod(data_str[1]);
        dst_chart(i, 1) = std::stod(data_str[2]);
        dst_chart(i, 2) = std::stod(data_str[3]);
        i++;
        if (i == 24) break;
    }
    return true;
}

void conv_sRGB2XYZ(const ChartType &rgb, ChartType &xyz) {
    Eigen::Matrix<double, 3, 3> M;
    M << 0.412391, 0.357584, 0.180481,
         0.212639, 0.715169, 0.072192,
         0.019331, 0.119195, 0.950532;
    xyz = (M * rgb.transpose()).transpose();
}

void SolveCCM(const ChartType& source_xyz, const ChartType& reference_xyz,
              CCMType &ccm) {
    // source_xyz * ccm == reference_xyz
    // (24, 3 + 1) * (4, 3) = (24 * 3)
    ChartHmType source_xyz_hm;
    source_xyz_hm.col(0) = source_xyz.col(0);
    source_xyz_hm.col(1) = source_xyz.col(1);
    source_xyz_hm.col(2) = source_xyz.col(2);
    source_xyz_hm.col(3) = Eigen::VectorXd::Ones(24);
    auto source_xyz_hm_t = source_xyz_hm.transpose();
    auto pinv = (source_xyz_hm_t * source_xyz_hm).inverse() * source_xyz_hm_t;
    ccm = pinv * reference_xyz;
}

void WriteCCM(const std::string &filename, const CCMType& ccm) {
    std::ofstream csv(filename);
    for (int i = 0; i < 4; i++) {
        csv << ccm(i, 0) << ","
            << ccm(i, 1) << ","
            << ccm(i, 2) << std::endl;
    }
}

bool ParseArgs(const int argc, char** argv, std::string& ref_csv,
               std::string& src_csv, std::string& out_csv, double& gamma) {
    args::ArgumentParser parser("Compute CCM.");
    args::HelpFlag help(parser, "help", "Display this help menu",
                        {'h', "help"});
    args::Positional<std::string> ref_csv_arg(parser, "reference",
                                              "reference csv file");
    args::Positional<std::string> src_csv_arg(parser, "source",
                                              "source csv file");
    args::Positional<std::string> out_csv_arg(parser, "output",
                                              "output csv file", "ccm.csv");
    args::ValueFlag<double> gamma_arg(parser, "gamma",
                                     "Gamma value of reference and source data",
                                     {'g', "gamma"}, 1.0);
    try {
        parser.ParseCLI(argc, argv);
    } catch (args::Help) {
        std::cout << parser;
        return false;
    } catch (args::ParseError e) {
        std::cerr << e.what() << std::endl;
        std::cerr << parser;
        return false;
    } catch (args::ValidationError e) {
        std::cerr << e.what() << std::endl;
        std::cerr << parser;
        return false;
    }
    if (!ref_csv_arg) {
        std::cout << "Error: reference is not set" << std::endl;
        std::cout << parser;
        return false;
    }
    if (!src_csv_arg) {
        std::cout << "Error: src is not set" << std::endl;
        std::cout << parser;
        return false;
    }

    ref_csv = args::get(ref_csv_arg);
    src_csv = args::get(src_csv_arg);
    out_csv = args::get(out_csv_arg);
    gamma = args::get(gamma_arg);

    return true;
}

int main(int argc, char** argv) {
    // Parse arguments
    std::string ref_csv, src_csv, out_csv;
    double gamma;
    if (!ParseArgs(argc, argv, ref_csv, src_csv, out_csv, gamma)) {
        return 1;
    }

    // Load color charts
    ChartType reference_raw, source_raw;
    if (!LoadColorchartCsv(ref_csv, reference_raw)) {
        return 1;
    }
    if (!LoadColorchartCsv(src_csv, source_raw)) {
        return 1;
    }

    // Degamma
    ChartType reference_linear = reference_raw.array().pow(gamma);
    ChartType source_linear = source_raw.array().pow(gamma);

    // XYZ
    ChartType reference_xyz, source_xyz;
    conv_sRGB2XYZ(reference_linear, reference_xyz);
    conv_sRGB2XYZ(source_linear, source_xyz);

    // Solve
    CCMType ccm;
    SolveCCM(source_xyz, reference_xyz, ccm);
    std::cout << "CCM:" << std::endl;
    std::cout << ccm << std::endl;

    // Save
    WriteCCM(out_csv, ccm);

    return 0;
}
