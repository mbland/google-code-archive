/* Stub declarations for inaccessible corecrypto functions */

#ifndef CORECRYPTO_CCEC_H
#define CORECRYPTO_CCEC_H

#define ccn_sizeof(N) 0
#define ccec_full_ctx_decl(X, Y) int Y
#define ccdh_gp_prime_size(X) sizeof(X) 
#define ccdh_gp_prime(X) sizeof(X) 
#define ccdh_gp_g(X) sizeof(X) 
#define ccdh_gp_rfc5114_MODP_2048_256() 0
#define ccdh_const_gp_t void*
#define ccdh_gp_n(X) sizeof(X) 
#define cc_size size_t

void ccn_write_uint(size_t, int, void*, void*);

#endif /* CORECRYPTO_CCEC_H */
