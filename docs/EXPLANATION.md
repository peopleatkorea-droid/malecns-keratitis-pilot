# A short explanation

I used a fixed visual subset of the male fruit fly connectome as an experimental image feature extractor. A corneal image was converted into grayscale stimulation, and a simplified simulation produced a pattern of neural activity. I counted responses in two time windows, reduced those features using training data, and trained a small logistic classifier to distinguish bacterial from fungal keratitis.

The fly circuit itself did not learn from the keratitis labels; only the final readout did. All images and visits from a patient stayed together during cross-validation. I compared the real wiring with the same raw input and ten rewired circuits to check whether the measured wiring added anything useful.

In this setup it did not: visit-level AUROC was approximately 0.48 for lesion crops and 0.46 for whole images. It was an enjoyable curiosity-driven experiment, with an underwhelming result.

## LinkedIn caption

For a bit of fun, I tried using a fruit fly connectome to classify bacterial versus fungal keratitis. 🪰

I converted corneal images into visual stimulation, ran them through a fixed, simplified simulation of the MaleCNS visual circuit, and trained a small classifier on the neural response patterns. The circuit stayed frozen; only the final classifier learned from the labels.

With patient-separated cross-validation across 111 patients, visit-level AUROC was about 0.48 for lesion crops and 0.46 for whole images — around chance. The real wiring also showed no convincing advantage over ten randomly rewired controls in this setup.

So, an interesting idea with an underwhelming result. I still enjoyed building it and checking whether the wiring itself contributed anything useful.

I've shared the experimental code under MIT, along with English methods, aggregate results, and a synthetic activity animation. Others can try their own images or explore different input and readout choices. The clinical images and fitted patient models remain private.

The animation shows simulated responses to a synthetic input. These results apply to this particular mapping, simulation, and readout; they don't establish a general limit of connectome-based approaches.

Thanks to the MaleCNS team for the dataset and the Fly OCR and DOOMFLY contributors for the simulation work this builds on.

Code: https://github.com/peopleatkorea-droid/malecns-keratitis-pilot
Project: https://tinystarlabs.com/#malecns-project
