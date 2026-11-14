// Thin standalone bridge to the unmodified, pinned MIT-licensed upstream OSD.
// No BP execution occurs here. Compile with the pinned source's src_cpp includes.
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include "osd.hpp"

struct Handle {
    ldpc::bp::BpSparse matrix;
    std::vector<double> probabilities;
    std::unique_ptr<ldpc::osd::OsdDecoder> decoder;
    Handle(int m, int n, const uint8_t* h, int depth, double p) : matrix(m, n), probabilities(n, p) {
        for (int row=0; row<m; row++) for (int col=0; col<n; col++)
            if (h[row*n+col]) matrix.insert_entry(row, col);
        decoder = std::make_unique<ldpc::osd::OsdDecoder>(matrix,
            depth ? ldpc::osd::COMBINATION_SWEEP : ldpc::osd::OSD_0, depth, probabilities);
        if (depth > decoder->k) throw std::invalid_argument("depth exceeds non-pivot count");
    }
};

static thread_local std::string error;
extern "C" const char* osd_error() {return error.c_str();}
extern "C" void* osd_create(int m, int n, const uint8_t* h, int depth, double p) {
    try {return new Handle(m,n,h,depth,p);} catch(const std::exception& e) {error=e.what();return nullptr;}
}
extern "C" void osd_destroy(void* value) {delete static_cast<Handle*>(value);}
extern "C" int osd_decode(void* value, const uint8_t* input, const double* llr,
                          uint8_t* selected, uint8_t* all_candidates) {
    try {
        auto& h=*static_cast<Handle*>(value);auto& d=*h.decoder;
        int m=h.matrix.m,n=h.matrix.n;
        std::vector<uint8_t> syndrome(input,input+m);
        std::vector<double> posterior(llr,llr+n);
        const auto& result=d.decode(syndrome,posterior);
        for(int col=0;col<n;col++)selected[col]=result[col];
        for(int row=0;row<m;row++) {
            uint8_t observed=0;
            for(const auto& entry:h.matrix.iterate_row(row))observed^=result[entry.col_index];
            if(observed!=syndrome[row])throw std::invalid_argument("inconsistent syndrome/native invalid output");
        }
        int count=1+static_cast<int>(d.osd_candidate_strings.size());
        if (!all_candidates) return count;
        for(int col=0;col<n;col++)all_candidates[col]=d.osd0_decoding[col];
        int index=1;
        const int rank=d.LuDecomposition->rank;
        for(const auto& pattern:d.osd_candidate_strings) {
            auto residual=syndrome;
            for(int i=0;i<d.k;i++) if(pattern[i])
                for(const auto& entry:h.matrix.iterate_column(d.LuDecomposition->cols[rank+i]))
                    residual[entry.row_index]^=1;
            auto candidate=d.LuDecomposition->lu_solve(residual);
            for(int i=0;i<d.k;i++)candidate[d.LuDecomposition->cols[rank+i]]=pattern[i];
            for(int col=0;col<n;col++)all_candidates[index*n+col]=candidate[col];
            index++;
        }
        return count;
    } catch(const std::exception& e) {error=e.what();return -1;}
}
