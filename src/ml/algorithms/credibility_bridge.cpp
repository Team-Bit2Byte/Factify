#include "scoring_engine.h"

#include <chrono>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>

using namespace factifycore;

namespace {

std::string json_escape(const std::string& input) {
    std::ostringstream out;
    for (char c : input) {
        switch (c) {
            case '"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\b': out << "\\b"; break;
            case '\f': out << "\\f"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                        << static_cast<int>(static_cast<unsigned char>(c))
                        << std::dec << std::setfill(' ');
                } else {
                    out << c;
                }
        }
    }
    return out.str();
}

std::unordered_map<std::string, std::string> parse_args(int argc, char* argv[]) {
    std::unordered_map<std::string, std::string> args;
    for (int i = 1; i + 1 < argc; i += 2) {
        args[argv[i]] = argv[i + 1];
    }
    return args;
}

std::string determine_verdict(double score) {
    if (score >= 80.0) {
        return "likely_original";
    }
    if (score >= 55.0) {
        return "unverified";
    }
    return "likely_fake_false";
}

}  // namespace

int main(int argc, char* argv[]) {
    const auto args = parse_args(argc, argv);

    const std::string headline = args.count("--headline") ? args.at("--headline") : "";
    const std::string body = args.count("--body") ? args.at("--body") : "";
    const std::string source = args.count("--source") ? args.at("--source") : "Unknown Source";
    const std::string sources_csv = args.count("--sources-csv") ? args.at("--sources-csv") : "";
    const std::string phrases_file = args.count("--phrases-file") ? args.at("--phrases-file") : "";
    const std::string negative_terms_file = args.count("--negative-terms-file") ? args.at("--negative-terms-file") : "";

    ScoringEngine engine;
    engine.initialize(sources_csv, phrases_file, negative_terms_file);

    Article article("factify-article", headline, body, source);
    CredibilityResult result = engine.assess_article(article);

    std::cout << "{";
    std::cout << "\"overall_score\":" << std::fixed << std::setprecision(2) << result.overall_score << ",";
    std::cout << "\"verdict\":\"" << determine_verdict(result.overall_score) << "\",";

    std::cout << "\"module_scores\":{";
    bool first = true;
    for (const auto& entry : result.module_scores) {
        if (!first) {
            std::cout << ",";
        }
        first = false;
        std::cout << "\"" << json_escape(entry.first) << "\":" << std::fixed << std::setprecision(2) << entry.second;
    }
    std::cout << "},";

    std::cout << "\"explanations\":[";
    for (size_t i = 0; i < result.explanations.size(); ++i) {
        if (i > 0) {
            std::cout << ",";
        }
        std::cout << "\"" << json_escape(result.explanations[i]) << "\"";
    }
    std::cout << "],";

    std::cout << "\"processing_time_ms\":" << result.processing_time.count();
    std::cout << "}";
    return 0;
}
