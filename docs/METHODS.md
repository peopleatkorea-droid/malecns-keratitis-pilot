# Experimental logic

## The question

Could responses from a measured fruit-fly visual wiring diagram provide useful features for distinguishing bacterial from fungal keratitis? Two joint primary comparisons tested whether the real wiring added value over the identical retinal input and over rewired circuits.

## The fixed circuit

The graph is an induced visual subset of MaleCNS v1.0: mapped R1-R6 photoreceptors, L1/L2/L3/L5 tonic inputs, optic-lobe intrinsic neurons, and visual projection neurons. There are 101,939 nodes, 11,757,352 directed connections, 3,335 retinal inputs, 7,114 tonic inputs, and 91,490 readout neurons. These are modeled connections, not a count of individually simulated synapses.

The retinal map is inferred by the upstream L1-L3 connectivity mapping and rescaled separately within each eye. Both eyes receive the full same image. Neurotransmitter predictions determine simplified connection signs, with the upstream positive fallback for unknown signs. These are engineering assumptions; receptor-specific effects, true visual angles, and fly spectral sensitivity are not reconstructed.

## Image to stimulation

The image is resized with aspect ratio preserved into a 128 by 128 canvas, using Lanczos interpolation and RGB (128,128,128) padding. Gamma-encoded sRGB luma uses weights (0.2126, 0.7152, 0.0722); color is discarded. The crop arm uses the archived soft-masked lesion crop, not a plain rectangular crop. The whole-image extension uses the full unmasked photograph.

The simulation uses the upstream simplified LIF kernel unchanged: 0.1 ms steps, 1.8 ms synaptic delay, 2.2 ms refractory period, and a 0.275 synapse-weight scale. Sensory gain is 20, lamina drive is 12, half-saturation is 0.2, and inversion is off. A 100 ms gray baseline at brightness 0.5 establishes the canonical state. Every image resets to this state, then is presented for 100 ms in twenty 5 ms bins.

## Responses to a classifier

Only the fixed non-directly-driven visual readout neurons are used. For each neuron, spike counts in 0-50 ms and 50-100 ms provide two features (182,980 raw features per image). `log1p` is applied per image. The visit analysis averages image features within a visit before training transformations. It does not average image classification probabilities to define the primary visit model.

Each training fold removes only features constant within that training set, fits a StandardScaler, fits a full-SVD PCA with 28 components and no whitening, then fits class-balanced logistic regression. The circuit weights are never trained on keratitis labels. The final classifier is supervised; this is not zero-shot classification.

## Comparators

The first pilot compares MedSigLIP text-28, MedSigLIP visual PCA-28, raw retinal brightness PCA-28, HOG PCA-28, the real circuit, ten independently rewired circuits, and a brightness/crop-size nuisance-feature model. Text-28 and nuisance features are scaled without an additional PCA. Archived MedSigLIP features are reused, while their classifiers are refitted under the common evaluation protocol.

Every rewired graph retains node identities, input/readout identities, directed in/out degrees, and signed connection strength by switching targets within exact signed-weight groups. Existing self-edges remain unchanged and duplicate connections are rejected. Seeds are 20260916-20260925, with five attempted sweeps per graph. Spatial distance, region-to-region connectivity, and activity matching are not preserved.

The synthetic activity guard requires each rewired graph's gray/checker readout total to be 0.1-10 times the real graph's total, with at least 28 active readout cells. All ten passed. This broad feasibility check excludes severe numerical collapse; it does not establish physiological or equal-activity matching.

## Evaluation

The cohort has 111 patients (69 bacterial, 42 fungal), 277 visits, and 720 white-light images. Fungal is label 1. All records of a patient remain together in five existing outer folds. Within each outer development set, four-fold StratifiedGroupKFold runs with three fixed seeds (20260916-20260918). The regularization grid is C = 0.001, 0.01, 0.1, 1, 10; ties prefer the smaller C. Scaling, constant-feature removal, and PCA are fitted anew in every inner training fold, then refitted on the complete development set for the outer test prediction.

The primary AUROC pools visit-level out-of-fold predictions. Uncertainty uses 5,000 paired patient-cluster bootstrap resamples of those fixed predictions. The rewired reference is the mean of the ten individual AUROCs, not the AUROC of averaged predictions. The exploratory continuation rule requires both real-minus-rewired-mean and real-minus-input 95% difference intervals to have positive lower bounds.

The whole-image extension uses the same patients, folds, fixed circuit, and ten rewired graphs. It fits image and visit classifiers separately. It was specified before its own OOF results were inspected, after crop results were already known; it remains an exploratory same-cohort extension.

## Interpretation

The dataset is a previously analyzed retrospective single-center culture-positive cohort. Repeated visits may include treatment. The first recorded visit is not guaranteed to be untreated presentation. Conditional bootstrap intervals do not account for all design selection or past dataset exposure. The circuit arm loses image color and resolution, so comparing it with MedSigLIP does not isolate wiring alone. Whole-image versus crop changes field of view, lesion scale, and masking at the same time.

The simulation is not physiologically validated. A neuron's name, activity, or classifier contribution does not demonstrate detection of a clinical sign. The low score is a result for this implementation, not a general finding about fruit-fly cognition.
