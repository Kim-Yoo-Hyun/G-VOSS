# Nonlinear Cross-Source Transfer Diagnostic

This diagnostic freezes the 69-parameter nonlinear rescorer trained on SGFN
internal-development exact labels and applies it unchanged to VL-SAT and
Open3DSG on the same official 3DSSG validation target. Target-source labels,
normalization, refitting, and hyperparameter changes are forbidden.

The purpose is to test whether the strong source-supervised comparator is also
a source-independent reliability layer. Results must be reported for both
targets and all frozen K values. This diagnostic cannot support dataset-level
generalization or prospective language.

## Result

Both Docker evaluations completed with all eight validations passing and the
serialized parameter, normalization, and training-trace payload identical to
the SGFN baseline. The frozen nonlinear rescorer does not transfer uniformly:

- VL-SAT: at K=100 it changes R/V from the strict family product
  `0.9690/0.0327` to `0.9625/0.0311`; the Recall delta is `-0.00655` with paired
  95% CI `[-0.01251,-0.00185]`. Recall is also significantly lower at every
  smaller K.
- Open3DSG: at K=100 it reaches `0.6166/0.0334`, statistically indistinguishable
  from the family product, but Recall collapses at K=5/10/20/50. At K=20 the
  delta is `-0.24673` with paired 95% CI `[-0.27444,-0.21903]`.

Thus the strong SGFN exact-label comparator is a useful source-adapted upper
bound, not a scale-stable source-independent replacement for the compatibility
factor.
