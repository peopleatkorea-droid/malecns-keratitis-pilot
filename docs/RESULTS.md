# Results of the keratitis pilot

The fixed first experiment did not meet the criterion for additional benefit from real MaleCNS wiring. The cohort contained 111 patients, 277 visits, and 720 white-light images. These are patient-disjoint internal cross-validation results, not external validation.

## Masked lesion crop

| Representation | Visit AUROC | Conditional patient-bootstrap 95% interval | First recorded visit AUROC |
| --- | ---: | --- | ---: |
| MedSigLIP text-28 | 0.735 | 0.649-0.809 | 0.649 |
| MedSigLIP visual PCA-28 | 0.754 | 0.670-0.828 | 0.684 |
| Retinal brightness PCA-28 | 0.464 | 0.364-0.566 | 0.493 |
| HOG PCA-28 | 0.571 | 0.469-0.664 | 0.540 |
| Real MaleCNS visual circuit | 0.479 | 0.385-0.565 | 0.434 |
| Brightness and crop-size control | 0.643 | 0.534-0.739 | 0.547 |

The ten rewired circuit AUROCs averaged 0.464, with range 0.426-0.539. The real graph exceeded seven of ten controls. The reference is a mean of individual model AUROCs, not a prediction ensemble.

| Predefined comparison | AUROC difference | Paired conditional 95% interval |
| --- | ---: | --- |
| Real wiring minus mean rewired wiring | +0.015 | -0.037 to +0.064 |
| Real wiring minus identical retinal input | +0.014 | -0.078 to +0.103 |

Neither lower bound exceeded zero. Activity feasibility checks passed for all ten controls. The negative result is consistent with no demonstrated added value in this setting; it does not establish equivalence.

| Rewiring seed | Visit AUROC | Conditional 95% interval |
| --- | ---: | --- |
| 20260916 | 0.431 | 0.349-0.516 |
| 20260917 | 0.523 | 0.422-0.615 |
| 20260918 | 0.439 | 0.346-0.532 |
| 20260919 | 0.436 | 0.342-0.525 |
| 20260920 | 0.445 | 0.356-0.539 |
| 20260921 | 0.426 | 0.340-0.512 |
| 20260922 | 0.494 | 0.403-0.579 |
| 20260923 | 0.465 | 0.374-0.556 |
| 20260924 | 0.539 | 0.454-0.624 |
| 20260925 | 0.438 | 0.348-0.525 |

## Whole-image extension

| Representation | Image AUROC (conditional 95% interval) | Visit AUROC (conditional 95% interval) |
| --- | --- | --- |
| Real MaleCNS, whole image | 0.476 (0.397-0.557) | 0.462 (0.383-0.544) |
| Real MaleCNS, masked crop | 0.461 (0.375-0.547) | 0.479 (0.385-0.565) |
| MedSigLIP whole visual-28 | 0.691 (0.604-0.769) | 0.701 (0.607-0.785) |
| MedSigLIP whole text-28 | 0.693 (0.607-0.771) | 0.693 (0.598-0.780) |
| Whole retinal brightness | 0.527 (0.446-0.612) | 0.556 (0.465-0.645) |
| Whole HOG | 0.455 (0.374-0.539) | 0.476 (0.380-0.578) |
| Whole brightness/image-size statistics | 0.433 (0.353-0.508) | 0.467 (0.359-0.566) |

The image classifier was fitted separately from the visit classifier. The crop image classifier was newly fitted in the extension; the crop visit predictions were reused unchanged from the first pilot.

| Unit | Comparison | Difference | Paired conditional 95% interval |
| --- | --- | ---: | --- |
| Image | Real minus mean rewired | +0.023 | -0.024 to +0.068 |
| Image | Real minus retinal input | -0.051 | -0.113 to +0.010 |
| Image | Whole minus crop | +0.014 | -0.098 to +0.130 |
| Visit | Real minus mean rewired | -0.002 | -0.067 to +0.064 |
| Visit | Real minus retinal input | -0.093 | -0.181 to -0.004 |
| Visit | Whole minus crop | -0.016 | -0.124 to +0.094 |

Neither unit met both joint comparison criteria. There was no consistent whole-versus-crop advantage. The visit real-minus-input interval was negative in this exploratory analysis; no confirmatory multiple-comparison claim is made.

Whole-image rewired means were 0.452 for images (range 0.418-0.488) and 0.464 for visits (range 0.431-0.536). The real graph exceeded nine of ten image controls and seven of ten visit controls. Exceeding several controls does not establish benefit when the paired comparison remains uncertain.

The whole-image visit model's first-recorded-visit AUROC was 0.498. The reference AUROC from averaging image-model probabilities within visits was 0.473; that is a different estimand from the separately fitted primary visit model.

## What can be concluded

The graph and simulation could be run, but this representation did not provide useful discrimination in the tested setup. It should not be proposed as a replacement for the foundation-model baseline on these results. Brightness/crop statistics showed some discrimination in the crop arm; this motivates checking acquisition and crop effects, without establishing a specific bias or cause.

## Limits of the evidence

- The cohort was previously analyzed, single-center, and restricted to culture-positive bacterial/fungal cases. There is no independent or prospective validation.
- The circuit is a selected visual subset with engineered input mapping and simplified dynamics. Color is discarded. Spatially matched rewiring controls were not evaluated.
- Bootstrap intervals condition on realized OOF predictions and fixed graphs; they do not cover all design choices or previous outcome exposure.
- The first recorded visit can be after treatment. Repeated-visit discrimination is not untreated-presentation diagnostic performance.
- Archived MedSigLIP features matched image/patient/visit/label identities and manifests. Historical input-byte hashes were unavailable, so byte identity with the original embedding inputs was not independently established.
- Scores come from class-balanced, uncalibrated readouts. They are not established clinical probabilities.

All released CSVs and JSONs contain aggregate metrics. Clinical source images, record mappings, per-patient predictions, embeddings, and trained models are kept private.
