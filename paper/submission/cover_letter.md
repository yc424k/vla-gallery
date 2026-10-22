[Date]

Editorial Office
*Applied Sciences* (MDPI)
Section: Robotics and Automation

Dear Editor,

I am pleased to submit the review article **"Training and Deployment Resources of Robot Vision–Language–Action Models: A Review of 215 Models with a Validated Feasibility Estimator"** for consideration in *Applied Sciences*, Section Robotics and Automation.

Vision–language–action (VLA) models have become a common way to build general-purpose robot policies, and dozens of them are released every year by academic laboratories and companies. Existing surveys describe their architectures and the techniques proposed to make them more efficient. They do not tell a robot developer how much a given model costs to train, whether it will run on a given onboard computer, or how often the necessary numbers are reported at all. This review addresses that gap with an applied, quantitative focus:

1. **An open, evidence-labelled dataset** of 215 robot policy models released between October 2022 and October 2026 (135 VLAs, 58 visuomotor policies and 22 related systems) across manipulation, humanoid whole-body control, mobile manipulation and navigation. Every value was taken from a primary source, every missing value is labelled as undisclosed or unverified, and each record was re-checked in a verification pass.
2. **A quantitative synthesis** of architecture and resource trends, including the shift from discrete-token to flow-matching action heads, the shift from Llama to Qwen backbones, training compute (from 24 to about 50,000 GPU-hours), training data, control rates, the use of reinforcement learning, and how policies command mobile bases.
3. **A disclosure audit** showing that only 18% of the models report enough to compute training GPU-hours and 13% report inference memory, and that industry-only models disclose eight of twelve resource items significantly less often than other models (Fisher's exact test, Holm-corrected).
4. **A roofline-based estimator** of inference latency, memory and fine-tuning cost, calibrated on 37 published latency measurements on 11 devices (median error 1.37×; 1.49× in leave-one-out validation), which we use to map which models can run at 10 Hz on devices from Jetson modules to an H100. The paper closes with a ten-item reporting checklist.

We believe the article suits the applied scope of *Applied Sciences*: its results are directly usable by engineers who must choose, fine-tune or deploy a robot foundation model under hardware constraints, and the dataset, analysis scripts and an interactive gallery are openly available.

This manuscript is original, has not been published previously, and is not under consideration for publication elsewhere. [TODO: if a preprint has been posted, state where.] The author declares no conflicts of interest. The use of generative AI tools is disclosed in the Materials and Methods and Acknowledgments sections, in accordance with MDPI policy.

Thank you for considering this submission.

Sincerely,

[Full name]
[Affiliation, address]
[E-mail] · [ORCID]
