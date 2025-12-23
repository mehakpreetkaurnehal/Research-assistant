## **What Your Features Reveal: Data-Efficient Black-Box Feature Inversion Attack** **for Split DNNs**

Zhihan Ren, Lijun He _[†]_, Jiaxi Liang, Xinzhu Fu, Haixia Bi, Fan Li
Xi’an Jiaotong University
Xi’an, 710049, China


_{_ renzh,liangjiaxi,xinzhufu _}_ @stu.xjtu.edu.cn, _{_ lijunhe,haixia.bi,lifan _}_ @mail.xjtu.edu.cn



**Abstract**


_Split DNNs enable edge devices by offloading intensive_
_computation to a cloud server, but this paradigm exposes_
_privacy vulnerabilities, as the intermediate features can be_
_exploited to reconstruct the private inputs via Feature In-_
_version Attack (FIA). Existing FIA methods often produce_
_limited reconstruction quality, making it difficult to assess_
_the true extent of privacy leakage. To reveal the privacy_
_risk of the leaked features, we introduce FIA-Flow, a_ _**black-**_
_**box**_ _FIA framework that achieves high-fidelity image re-_
_construction from intermediate features. To exploit the se-_
_mantic information within intermediate features, we de-_
_sign a Latent Feature Space Alignment Module (LFSAM)_
_to bridge the semantic gap between the intermediate fea-_
_ture space and the latent space. Furthermore, to rectify dis-_
_tributional mismatch, we develop Deterministic Inversion_
_Flow Matching (DIFM), which projects off-manifold fea-_
_tures onto the target manifold with_ _**one-step inference**_ _. This_
_decoupled design simplifies learning and enables effective_
_training with_ _**few image–feature pairs**_ _. To quantify privacy_
_leakage from a human perspective, we also propose two_
_metrics based on a large vision-language model. Experi-_
_ments show that FIA-Flow achieves more faithful and se-_
_mantically aligned feature inversion across various models_
_(AlexNet, ResNet, Swin Transformer, DINO, and YOLO11)_
_and layers, revealing a more severe privacy threat in Split_
_DNNs than previously recognized._


**1. Introduction**


Deep neural networks (DNNs) have demonstrated remarkable performance in various applications, including autonomous driving [3, 37], smart security [27, 28, 36], and
smart mobile devices [8, 21, 39, 42]. Although performance
gains are largely driven by increasing model scale and
architectural complexity [14], the resulting computational
demands render on-device implementation impractical for



**(c) Pipeline of Proposed FIA-Flow**


Figure 1. (a) The pipeline of Split DNNs, which exposes intermediate features and creates an attack surface. (b) Existing FIA
methods achieve inversion via white-box, sample-specific iterative feature matching for each input. (c) In contrast, FIA-Flow is
trained once on a proxy dataset, learning to perform fast one-step
inversion for any unseen input.


resource-constrained edge devices. To offload the majority
of computation to cloud servers, Split DNNs have been proposed [13, 45], which divide a DNN into a lightweight head
submodel on edge devices and a computationally intensive
tail submodel on cloud servers, as shown in Fig. 1(a). The
effectiveness of split computing critically depends on identifying optimal partition points that balance edge computation, cloud processing, and communication overhead across
different model architectures and edge device capabilities.

Beyond computational efficiency, split computing is often regarded as a privacy-preserving technique, as raw input



**Edge Device** **Cloud Server**







**Intermediate**

**Features**





**(a) Pipeline of Split DNNs**













**(b) Pipeline of the existing FIA method**








Table 1. Key characteristics and capabilities of various FIA methods. [†] and [‡] denote the different settings of DMB.


Black-Box Efficient Model Applicability
Method
Attack Inference (Training Numbers)
M&V [32] ✘ ✘ Sample-Specific
DIP [5] ✘ ✘ Sample-Specific
SG-DIP [24] ✘ ✘ Sample-Specific
DRAG [20] ✘ ✘ Sample-Specific
AR [40] ✘ ✔ General (1 _._ 28M)
DIA [2] ✔ ✘ General (40 _,_ 000)
DMB [†] [53] ✔ ✘ General (4 _,_ 096)
DMB [‡] [53] ✘ ✘ Sample-Specific


data remains on the client’s local device [1, 13, 15, 34, 44].
However, with the enhanced capabilities of image generation [16, 17], this assumption requires serious reconsideration. While classic model inversion attacks (MIA)

[12, 22, 23, 30, 50, 55] exploit final model outputs to reconstruct **training data**, split computing exposes intermediate
feature representations during transmission, creating a more
direct and vulnerable attack surface. The potential adversaries include malicious attackers intercepting transmitted
features and curious cloud servers analyzing user features
beyond their intended computational scope.

This gives rise to the feature inversion attack (FIA),
which aims to reconstruct the **original input images** from
intermediate features. Despite growing research interest in
this threat model, existing FIA methods face three limitations (shown in Fig. 1(b) and Table 1): **(i) White-box**
**assumptions** : Most existing approaches assume white-box
access to model architectures and weights [5, 20, 24, 32,
40], limiting their generalization to diverse real-world split
computing deployments. **(ii) Heavy data dependence** :
Learning-based methods [2, 53] typically require extensive
training datasets with paired features and ground-truth images, which are difficult to obtain in realistic scenarios. **(iii)**
**High computational cost** : Optimization-based approaches

[5, 20, 24, 32, 53] require thousands of iterative optimization steps per sample, making real-time attacks infeasible
and easily detectable due to excessive query patterns.

To address these limitations, we propose **FIA-Flow**, a
_black-box_ FIA framework built on an alignment-refinement
paradigm that simultaneously achieves _one-step inference_
and _data-efficient training_, as shown in Fig. 1(c). Specifically, the alignment stage employs a Latent Feature Space
Alignment Module (LFSAM) that bridges the semantic gap
between task-specific intermediate features and generative
latent spaces. LFSAM progressively fuses multi-channel
information and adapts to diverse network layers and architectures, mapping the intermediate feature into a structurally aligned latent representation. Furthermore, the re


finement stage develops the Deterministic Inversion Flow
Matching (DIFM), inspired by flow-matching (FM) [26].
Unlike conventional generative models [29, 56], DIFM
learns a deterministic vector field to project these coarsely
aligned features onto the natural data manifold, correcting
distributional mismatch and recovering fine-grained visual
details. Crucially, FIA-Flow operates in a black-box setting, requiring only query access to intermediate features,
and can be trained effectively with a small collection (fewer
than 4 _,_ 096 image-feature pairs, i.e., _<_ 0 _._ 32% of ImageNet1K), making it highly practical for real-world split computing scenarios. The main contributions are as follows:

- **Black-box FIA framework** : We propose FIA-Flow, a
black-box FIA framework that can eliminate iterative optimization without requiring access to the victim model,
thereby revealing the risks present in split computing.

- **Data-efficient alignment-refinement strategy** : We decouple the FIA task into a two-stage paradigm combining
LFSAM for cross-space feature mapping and DIFM for
distributional correction with few samples.

- **One-Step Inference via DIFM** : We develop DIFM that
learns a deterministic vector field to enable high-fidelity
reconstruction in a single forward pass, eliminating the
iterative optimization of optimization-based methods and
multi-step sampling of diffusion-based FIA models.


**2. Method**


**2.1. Overview and Problem Formulation**


Let _M_ : _X →F_ denote the head submodel of the victim
Split DNN system, where _X ⊆_ R _[H][×][W][ ×][C]_ is the space of
private input images. For a given input _x ∈X_, the model
_M_ produces an intermediate feature _f_ = _M_ ( _x_ ) at a specific split layer, where _f ∈F ⊆_ R _[D][f]_ and _Df_ is the feature dimension. The primary objective of FIA is to learn
an inversion mapping _G_ : _F →X_ that can reconstruct the
original input _x_ _[′]_ from its corresponding feature _f_, such that
the reconstructed image _x_ _[′]_ = _G_ ( _f_ ) _≈_ _x_ is perceptually and
semantically indistinguishable from the original input _x_ .
Our attack operates under a black-box assumption,
where the architecture and parameters of _M_ are unknown.
We can only query to obtain a set of image-feature pairs
_D_ = _{_ ( _xi, fi_ ) _}_ _[N]_ _i_ =1 [for training. To achieve this, FIA-Flow]
adopts an alignment-refinement strategy, as shown in Fig. 2.
We decouple the complex inversion mapping _G_ into a twostage process: a structural alignment stage and a semantic
refinement stage, which can be formulated as:


_x_ _[′]_ = _G_ ( _f_ ) = Dec( _G_ refine( _G_ align( _f_ ))) (1)


Dec : _Z →X_ denotes the decoder of Variational Autoencoder (VAE) [18]. The alignment stage _G_ align : _F →Z_
establishes structural correspondence by aligning the taskrelevant feature spaces and latent space of the VAE. How

**Attack Result**













Figure 2. The pipeline of FIA-Flow. The method reconstructs a private image _x_ from the corresponding intermediate features _f_ . It first
maps _f_ to a latent code _zs_ by the Latent Feature Space Alignment Module, then uses the Deterministic Inversion Flow Matching module
to refine it into ˆ _zx_ . Finally, the attack image _x_ _[′]_ is obtained by a pre-trained VAE decoder from ˆ _zx_ .



ever, this alignment primarily yields an off-manifold representation, which lacks the semantic richness. Therefore, the
refinement stage _G_ refine : _Z →Z_ performs intra-space semantic enhancement, correcting the distributional mismatch
to ensure high-fidelity inversion.


**2.2. Latent Feature Space Alignment Module**


**Motivation and Objective** A fundamental challenge in
FIA arises from the space gap between _F_ and the latent
space _Z_ . Since _F_ is task-specific and optimized for classification rather than synthesis, its structure is inherently incompatible with the manifold of _Z_ [51]. Therefore, a direct
mapping from feature _f_ to image _x_ is ill-posed. To bridge
this gap, we propose the LFSAM to transform a given intermediate feature _f_ into a latent tensor _zs_ = _G_ align( _f_ ), which
is designed to be both dimensionally compatible and structurally aligned with the latent space of VAE. The VAE is
selected for its continuity and structured latent space, offering an ideal manifold for stable and coherent refinement

[6]. Meanwhile, the low-dimensional latent space reduces
the complexity of the hypothesis class, making alignment
learning easier to generalize under few-sample conditions

[48]. This enables FIA-Flow to effectively learn and extrapolate robustly to unseen features.


**Cross-Space Feature Alignment** LFSAM comprises a
learned upsampling module, a backbone, and a Feature
Aggregation Network (FAN) to synthesize a comprehensive latent representation. To accommodate features with
varying resolutions across different network layers, we
employ a PixelShuffle-based spatialization layer _PS_ :



R [(] _[r]_ [2] _[C][in][×][H][in][×][W][in]_ [)] _→_ R [(] _[C][in][×][rH][in][×][rW][in]_ [)] . Unlike standard interpolation, this operation provides a learned transformation that unfolds channel-encoded spatial information
into an explicit geometric grid.
The backbone _B_ ( _·_ ) processes _f_ through a hierarchical encoder, which extracts a set of feature maps
_{e_ 1 _, e_ 2 _, . . ., eL}_ . Its corresponding decoder reconstructs
the output progressively from the deepest feature level. Crucially, at each stage, the decoder integrates features from the
corresponding encoder stage via skip connections, a process
formulated as _di_ +1 = _D_ ( _concat_ ( _di, ei_ )). To capture global
context and long-range spatial dependencies, we embed
self-attention mechanisms within the backbone layers, producing _Fd_ = _B_ ( _f_ ). Meanwhile, FAN projects each _ei_ into
a shared space via 1 _×_ 1 convolutions _ϕi_ then concatenates
and fuses them: _Ffan_ = Convfuse(concat _[L]_ _i_ =1 [(] _[ϕ][i]_ [(] _[e][i]_ [)))][. The]
final aligned feature is:


_zs_ = Convout( _Fd_ + _Ffan_ ) _,_ (2)


which serves as a structural alignment feature for the subsequent refinement stage.


**2.3. Deterministic Inversion Flow Matching**


**Motivation and Objective** With the space-aligned latent
feature _zs_ obtained from LFSAM, we aim to generate a
photorealistic inversion image _x_ _[′]_ that closely resembles the
private input _x_ . A naive approach involves directly decoding the aligned feature _zs_ using a pre-trained VAE decoder
_x_ _[′]_ = Dec( _zs_ ). However, experimental results demonstrate
that this straightforward method produces suboptimal results with severe blurriness and semantic inconsistencies.


The core issue is a distributional mismatch between the
aligned features and the natural data manifold. Although
LFSAM ensures that _zs_ conforms to the dimensional requirements of the VAE latent space, it fails to guarantee that
_zs_ follows the same distribution as the authentic latent feature generated by the VAE encoder from natural images.
Since _zs_ originates from a task-specific feature transformation, it likely resides in off-manifold regions of the latent
space _Z_ . The VAE decoder is trained exclusively on onmanifold samples, cannot interpret out-of-distribution inputs, resulting in degraded reconstruction quality. Therefore, we propose the DIFM to enhance semantic expressiveness based on the previous structural alignment.


**Intra-Space Feature Enhancement** To overcome the
limitations of direct decoding, we reframe _zs_ as a highquality starting point for a generative process rather than
a final latent feature. We employ the DIFM to learn a deterministic vector field _vθ_ ( _z, t_ ) that transforms the distribution
of our structurally-aligned features _p_ 0 = _p_ ( _zs_ ) to the target
data distribution _p_ 1 = _p_ ( _zx_ ), where _zx_ = Enc( _x_ ). This approach adapts the standard FM framework by replacing the
conventional Gaussian prior _p_ _[′]_ 0 [=] _[ N]_ [(0] _[, I]_ [)][ with our mean-]
ingful initializations _p_ ( _zs_ ).
Specifically, we define a linear interpolation path between the starting point _zs_ and its corresponding target _zx_
as _zt_ = _t · zx_ + (1 _−_ _t_ ) _· zs_ for _t ∈_ [0 _,_ 1]. DIFM is trained
to approximate this target field _ut_ = _dzt/dt_ = _zx −_ _zs_ .
Once trained, this learned vector field defines the trajectory of each point via the probability flow ordinary differential equation (ODE), _dz_ ˆ _t/dt_ = _vθ_ (ˆ _zt, t_ ), and the continuity
equation describes its distributional evolution:


_∂tpt_ ( _z_ ) + _∇z ·_ ( _pt_ ( _z_ ) _vθ_ ( _z, t_ )) = 0 _._ (3)


This equation formalizes the desired behavior of _vθ_ ( _z, t_ ),
ensuring it guides the population of points from the initial
distribution _p_ 0 to the target data distribution _p_ 1. Since LFSAM already produces _zs_ close to _zx_, the learned vector
field is simple, allowing us to replace an expensive ODE
solver with a single forward Euler step from _t_ = 0 to _t_ = 1:


_z_ ˆ _x_ = ˆ _z_ 1 = _zs_ + _vθ_ ( _zs, t_ = 0) _._ (4)


The final inversion image _x_ _[′]_ is decoded by the VAE:
_x_ _[′]_ = Dec(ˆ _zx_ ). By conditioning the generative process on
a meaningful initialization, our strategy effectively transforms a complex generation task into a residual correction
problem. This simplifies the learning dynamics of the vector field, reducing the data requirements, thereby enabling
high-fidelity inversion even with limited training samples.


**2.4. Training Strategy**


We adopt a two-stage training paradigm for the FIA task.
This decoupled approach is designed first to establish a



space alignment and then to optimize the generative model.
**Stage 1: Training the LFSAM.** In the first stage, we train
the LFSAM to learn a mapping from the task-relevant input features _f_ to the VAE latent space. Our objective is to
ensure that the LFSAM produces structured features _zs_ that
closely approximate the ground truth (GT) VAE latent feature _zx_ of the corresponding images _x_ . We employ a pretrained, frozen VAE encoder to obtain target latent codes
_zx_ = Enc( _x_ ). To ensure feature space alignment, we minimize the L2 distance between the _zs_ and _zx_ :


_L_ fea = E( _x,f_ ) _∼D_     - _∥zs −_ _zx∥_ [2] 2� _._ (5)


To enforce perceptual coherence, we apply an imagedomain reconstruction loss. We decode the generated latent
_zs_, and minimize the L1 distance to the GT image _x_ :


_L_ img = E( _x,f_ ) _∼D_ [ _∥_ Dec( _zs_ ) _−_ _x∥_ 1] _._ (6)


The total loss for Stage 1 is the sum of these two losses:


_L_ s1 = _L_ fea + _L_ img _._ (7)


Stage 1 ensures that the LFSAM learns a meaningful
projection into the VAE latent space, providing a solid foundation for the subsequent stage.
**Stage 2: Training the DIFM.** In the second stage, we
freeze the LFSAM and train the DIFM, which takes the precomputed features _zs_ as a starting point and learns to generate the final image _x_ _[′]_ . The training objective for this stage
is a combination of two losses:
1. **Flow Matching Loss (** _L_ **fm):** This is a regression loss
that minimizes the L2 distance between the model’s predicted vector field _vθ_ ( _zt, t_ ) and the target vector field _ut_ :


_L_ fm = E _t∼U_ [0 _,_ 1] _,_ ( _x,f_ ) _∼D_   - _∥vθ_ ( _zt, t_ ) _−_ _ut∥_ [2] 2� _._ (8)


2. **Reconstruction Loss (** _Lrec_ **):** To ensure that the final
output _x_ _[′]_ is perceptually and semantically faithful to
the original image _x_, we apply a reconstruction loss directly in the image space. This loss is a combination of
Learned Perceptual Image Patch Similarity (LPIPS) [52]
loss and a pixel-wise L1 loss:


_L_ rec = E( _x,f_ ) _∼D_ [ _L_ LPIPS( _x_ _[′]_ _, x_ ) + _L_ L1( _x_ _[′]_ _, x_ )] _._ (9)


The final loss for Stage 2 is the sum of these two losses:


_L_ s2 = _L_ fm + _L_ rec _._ (10)


**3. Experiments**


**3.1. Datasets and Metrics**


Our experiments were conducted on a subset of ImageNet1K [4]. Specifically, we randomly sample only 4,096 images ( _<_ 0 _._ 32%) from the training set for training and 1,000
images from the validation set for testing.


Expert,” an image analysis specialist. **Image** **`]:`** Expert,” an image analysis specialist. **Image** **`]:`**

















**LVLM-PL** _**=**_ BERTScore( { _**original_detailed_description**_ }, { _**inversion_detailed_description**_ } ) **= 0.920**


Figure 3. An illustration of LVLM-C and LVLM-PL evaluation. ① The LVLM is prompted to describe the original image. ② The LVLM is
then prompted to describe the inversion image. ③ The LVLM compares these two descriptions to ascertain if the same object is identified. A
consistent result yields the LVLM-C value of 1. ④ LVLM-PL is obtained by computing the BERTScore [54] between the two descriptions.



We employ a comprehensive set of Image Quality Assessment (IQA) metrics. For full-reference IQA, we use
the Peak Signal-to-Noise Ratio (PSNR), Structural Similarity Index Measure (SSIM), and LPIPS [52]. For noreference IQA, we utilize the Natural Image Quality Evaluator (NIQE) [33] and MANIQA [49]. Furthermore, to
measure the eavesdropping information accuracy, we assess the inversion image top-1 classification accuracy ( **Acc** )
with the GT label of the original image, using ResNet-50

[7]. To assess private information leakage, we propose two
novel metrics evaluated by Large Vision-Language Models (LVLMs): LVLM-Consistency ( **LVLM-C** ) and LVLMPrivacy-Leakage ( **LVLM-PL** ). As shown in Fig. 3, the
LVLM acts as an _Image Description Expert_, generating textual descriptions for both the original and inversion images. These descriptions are compared by an _Image Leak_
_Inspector_ to determine whether they depict the same primary object (LVLM-C) and to compute their semantic similarity via BERTScore [54] (LVLM-PL). Higher LVLM-C
and LVLM-PL values indicate that the attacker can extract
more detailed private information from the inversion image. In our implementation, we utilize _gpt-4o-mini_ as the
LVLM. See supplementary materials for the detailed calculation process and an ablation study with other LVLM.


**3.2. Implementation Details**


We selected _features.10_ (F-10) of AlexNet [19], _layer1.2_
(L1-2) and _layer4.2_ (L4-2) of ResNet-50 [7], _fea-_
_tures.3.0.mlp.2_ (F3-2) of Swin Transformer (Swin-B) [31],
_model.8_ (M-8) of YOLO11n [11], and _blocks.11_ (B-11) of



DINOv2-B [35] as the victim layers and models for FIA.
The DIFM is initialized with the pre-trained weights of Stable Diffusion 2.1 [41]. To adapt it for the FIA task, we
freeze the U-Net in the DIFM and integrate a Low-Rank
Adaptation (LoRA) [10] model with a rank of _r_ = 4. For
both stages, we set the batch size to 8 and the learning rate
to 0 _._ 0001, with each stage trained for 64 _,_ 000 iterations. All
experiments were conducted on NVIDIA A100 GPUs.


**3.3. Main results**


We compare the proposed FIA-Flow with state-of-the-art
FIA methods, including M&V [32], Deep Image Prior
(DIP) [5], Adversarially Robust (AR) [40], Self-Guided
DIP (SG-DIP) [24]. Additionally, we compared against a
baseline FIA-Align that solely employs LFSAM for feature
space alignment, followed by VAE decoding.


**Quantitative Results** Table 2 shows the results of different FIA methods for various victim models and layers. For
AlexNet, FIA-Flow achieves an Acc of 28.8%, showing a
significant advantage over other methods. For ResNet-50,
when dealing with information-rich shallow features (L12), FIA-Flow can achieve an outstanding Acc of **71.3%** .
This performance remains robust even when dealing with
deep features from the L4-2 layer, which typically suffer
from substantial information loss. While other methods experience a dramatic degradation in image quality, leading to
significant drops in both Acc and LVLM-based evaluations,
FIA-Flow maintains an Acc of 36.8% and an LVLM-PL of
0.902. Furthermore, experiments on the Swin Transformer


Table 2. The performance comparison among different FIA methods. Bold indicates the best result of all methods.


Model Layer Method PSNR _↑_ SSIM _↑_ LPIPS _↓_ Acc _↑_ LVLM-C _↑_ LVLM-PL _↑_ NIQE _↓_ MANIQA _↑_



AlexNet F-10


L1-2


ResNet-50


L4-2


Swin-B F3-2


YOLO11n M-8


DINOv2-B B-11



M&V 13.55 0.500 0.730 0.0 1.2 0.860 5.853 0.4303
DIP 15.45 0.422 0.585 16.1 10.6 0.880 5.988 0.2763
AR 18.65 0.508 0.574 4.1 4.8 0.880 5.874 0.3258
SG-DIP 11.07 0.257 0.778 1.2 3.6 0.865 **5.603** 0.2950
FIA-Align 20.46 **0.607** 0.620 5.7 9.3 0.883 10.927 0.2959
FIA-Flow **20.64** 0.603 **0.405** **28.8** **16.6** **0.900** 6.243 **0.4956**


M&V 13.83 0.603 0.593 13.4 17.5 0.903 5.392 0.4938
DIP 25.73 0.706 0.236 61.0 39.9 0.905 5.504 0.4565
SG-DIP 27.90 0.754 0.193 65.2 65.3 0.922 5.301 0.4928
FIA-Align 29.86 0.810 0.157 64.3 70.0 0.923 5.136 0.5622
FIA-Flow **30.01** **0.814** **0.100** **71.3** **70.1** **0.929** **4.408** **0.6131**


M&V 13.55 0.504 0.851 0.0 3.0 0.860 7.577 0.4359
DIP 13.60 0.453 0.711 27.3 9.4 0.881 7.152 0.2592
SG-DIP 11.59 0.309 0.777 8.1 5.0 0.872 5.603 0.3189
FIA-Align **20.36** **0.603** 0.643 4.4 6.3 0.878 11.309 0.2969
FIA-Flow 20.31 0.584 **0.397** **36.8** **18.0** **0.902** **5.098** **0.5628**


M&V 14.34 0.628 0.541 38.1 38.4 0.913 6.105 0.4465
DIP 21.03 0.735 0.313 61.7 54.5 0.920 5.486 0.4492
SG-DIP 25.15 **0.872** 0.191 68.5 62.3 0.913 5.520 0.5362
FIA-Align 26.64 0.771 0.260 53.6 51.5 0.919 6.236 0.4725
FIA-Flow **27.29** 0.780 **0.159** **70.6** **63.2** **0.925** **4.840** **0.5777**


M&V 7.59 0.239 0.890 0.3 1.2 0.863 6.715 0.4702
DIP 14.09 0.521 0.572 14.6 18.2 0.897 6.796 0.4168
SG-DIP 14.04 0.518 0.582 12.1 18.1 **0.899** 6.696 0.4124
FIA-Align 20.56 **0.612** 0.627 4.1 7.1 0.880 11.056 0.2958
FIA-Flow **20.90** 0.608 **0.437** **23.6** **23.9** **0.899** **6.528** **0.4968**


M&V 13.53 0.477 0.868 0.1 0.7 0.855 13.533 0.3324
DIP 13.45 0.493 0.833 1.3 4.9 0.868 8.497 0.3316
SG-DIP 12.42 0.345 0.741 17.7 28.3 0.905 5.838 0.3662
FIA-Align 19.92 0.619 0.609 9.2 16.7 0.890 10.340 0.2709
FIA-Flow **20.13** **0.621** **0.411** **42.8** **30.4** **0.909** **6.304** **0.5079**



model (Swin-B), object detection model (YOLO11n), and
foundation model (DINOv2-B) confirm the superiority of
FIA-Flow, highlighting its broad applicability and effectiveness across diverse model architectures.


Benefiting from the alignment-refinement strategy, FIAFlow not only achieves a higher inversion quality on
IQA metrics but also exhibits substantially better semantic
preservation, as validated by Acc and LVLM-based metrics.
This proves that FIA-Flow constitutes a more effective and
practical privacy threat.


**Qualitative Results** As shown in Fig. 4, our FIA-Flow
outperforms other methods on both ResNet-50, Swin-B,
YOLO11n, and DINOv2. While other methods fail or produce blurry results, FIA-Flow can invert images with exceptional clarity, accurately capturing fine details like the face,
wireless router, and lighthouse. This visually confirms its
state-of-the-art performance and robustness across diverse
architectures. More visual results are available in the Supplementary Materials.



**Robustness Evaluation Under Defenses** To verify the
robustness of FIA-Flow under different defense mechanisms, we evaluate all methods against two representative
defenses: Noise+NoPeek [46] and DISCO [43], as shown
in Table 3 and Fig. 5. Under the Noise+NoPeek defense,
where Laplacian noise is injected into intermediate features
and a NoPeek strategy [47] is employed to restrict information leakage, FIA-Flow still outperforms other methods.
Similarly, under the DISCO defense, which suppresses intermediate features, FIA-Flow remains effective, recovering the original image with minimal samples. This demonstrates that FIA-Flow can effectively bypass defense mechanisms and extract sensitive information, even in a blackbox setting, without access to the defense’s implementation
details and model parameters.


**Generalization Evaluation Across Diverse Datasets**
We evaluate on the MS COCO-2017 dataset [25] to demonstrate the generalization capability of FIA-Flow (See Table 4). To quantify privacy leakage beyond standard IQA,
we introduce the **Object Reconstruction Rate (ORR)**,
which measures the consistency between the outputs of


**ResNet-50**

**L4-2**


**Swin-B**

**F3-2**


**YOLO11n**

**M-8**


**DINOv2**

**B-11**


**Original Feature**


**DIP**


**Original Feature**


**DIP**



**Defended Feature**


**SG-DIP**


**Defended Feature**


**SG-DIP**



**Feature** **GT** **M&V** **DIP** **SG-DIP** **FIA-Align** **FIA-Flow**


Figure 4. Visualization comparison of different FIA methods on various models.


Table 3. Robustness comparison under different defense mechanisms of Split DNNs on the L1–2 layer of ResNet-50.


Defense Methods PSNR _↑_ Acc _↑_ LVLM-C _↑_ LVLM-PL _↑_



**GT**


**FIA-Align**


**GT**


**FIA-Align**



**M&V**


**FIA-Flow**


**M&V**


**FIA-Flow**



Noise
+
NoPeek

[46]


DISCO

[43]



M&V 13.56 0.0 2.1 0.861
DIP 21.87 26.9 41.5 0.921
SG-DIP 21.69 53.3 49.1 0.919
FIA-Align 26.05 38.3 45.8 0.911
FIA-Flow **27.70** **62.2** **55.0** **0.922**


M&V 13.57 0.1 1.0 0.860
DIP **27.10** 35.9 39.6 0.914
SG-DIP 26.02 43.7 39.8 0.910
FIA-Align 26.49 37.4 38.7 0.913



Figure 5. Visualization comparison on different defense mechanisms. Top row: visualizations under the Noise+NoPeek defense

[46]. Bottom row: visualizations under the DISCO defense [43].


a pre-trained detector (Faster R-CNN [38]) on the original and inverted images. Trained only on ImageNet
and without fine-tuning on COCO, FIA-Flow achieves
state-of-the-art performance compared to methods that re


quire sample-specific optimization on target features. This
cross-dataset generalization is mainly attributed to the
alignment–refinement design of FIA-Flow, which learns a
dataset-agnostic mapping from task features to the VAE latent space. High ORR obtained by FIA-Flow indicates that
the inverted images retain task-relevant semantics for downstream models, revealing a stronger privacy risk than IQA
metrics alone capture. The definition of ORR and the complete results are shown in the Supplementary Materials.


**3.4. Ablation Studies**


We report the main ablation results on attack-layer robustness, data efficiency, and the diffusion sampling methods
and steps in the main paper. Additional ablations and complete results are shown in the Supplementary Materials.


Table 4. The performance comparison with different FIA methods
on the COCO dataset. Bold indicates the best result of all methods.


Method LPIPS _↓_ MANIQA _↑_ ORR0 _._ 5 _↑_ ORR0 _._ 75 _↑_

M&V 0.700 0.5191 3.30 2.20
DIP 0.332 0.4464 44.94 33.40
SG-DIP 0.284 0.4834 50.41 39.75
FIA-Align 0.195 0.5981 56.02 45.84


Figure 6. (a) Left: Performance comparison on the L4-2 layer with
different training numbers of FIA-Flow. (b) Right: Performance
comparison at different layers.


**Results on Different Training Numbers** To test data
efficiency, we trained on the ResNet-50 L4-2 layer using datasets ranging from 4,096 (0.32%) down to just **128**
**(0.01%)** samples, shown in Table 5 and Fig. 6(a). Using
only 128 samples (0.01%), FIA-Flow not only achieves a
high Acc of 27.7% but also outperforms other methods. The
data efficiency can be attributed to LFSAM, which enforces
structural alignment with the latent space through feature
rearrangement that matches its dimensionality and hierarchical aggregation that reduces the mapping complexity and
sample requirements.


**Results on Different Layers** We evaluate FIA-Flow at
various depths of ResNet-50, shown in Table 6 and Fig.
6(b). While performance degrades in deeper layers, FIAFlow consistently outperforms other methods across all victim layers. Notably, its performance on the deep L3-2 layer
( **69.8%** Acc) exceeds SG-DIP’s 65.2% on the shallow L12 layer. Despite the loss of spatial detail in deeper layers,
FIA-Flow effectively uses high-level semantic information
for accurate reconstruction. This capability underscores a
serious privacy concern: FIA-Flow can recover visually detailed and semantically meaningful images from abstract
representations.


**Results on Different Sampling Methods and Steps** The
performance gap between diffusion probabilistic model
(DDPM) [9] and DIFM reflects not only efficiency but
also methodological suitability for FIA. The iterative “addnoise, then-denoise” paradigm of DDPM is an indirect and



Table 5. The performance comparison of FIA-Flow with different
training numbers on L4-2 of ResNet-50.


Number PSNR _↑_ Acc _↑_ LVLM-C _↑_ LVLM-PL _↑_


4,096(0.32%) 20.31 36.8 18.0 0.902
1024(0.08%) 20.04 27.7 14.5 0.898
256(0.02%) 19.45 31.1 12.8 0.900
128(0.01%) 19.01 27.7 12.5 0.898


Table 6. The performance comparison of FIA-Flow across different victim layers of ResNet-50.


Layer PSNR _↑_ Acc _↑_ LVLM-C _↑_ LVLM-PL _↑_


L1-2 30.01 71.3 70.1 0.929
L2-2 29.65 71.0 69.8 0.928
L3-2 26.29 69.8 63.4 0.913
L4-2 20.31 36.8 18.0 0.902


Table 7. The performance comparison of FIA-Flow with different
sampling methods and steps on L4-2 of ResNet-50.


Methods Steps PSNR _↑_ Acc _↑_ LVLM-C _↑_ LVLM-PL _↑_


10 20.09 4.1 5.8 0.878
DDPM 50 19.97 4.9 4.2 0.876
200 19.95 4.5 4.8 0.877


1 **20.31** 36.8 18.0 0.902
DIFM 5 19.61 **38.2** 37.3 **0.914**
10 19.21 36.9 **38.3** **0.914**


stochastic process designed for diverse sampling, making
it difficult for the high-fidelity reconstruction of a specific input. In contrast, FIA-Flow adopts a deterministic
alignment-refinement paradigm, enabling efficient, highfidelity inversion. As shown in Table 7, one-step DIFM
is highly effective. Increasing sampling steps slightly decreases PSNR but improves Acc and LVLM-based scores,
suggesting increased privacy exposure.


**4. Conclusion**


In this work, we introduce FIA-Flow, a data-efficient blackbox FIA framework for high-fidelity feature inversion in
Split DNNs. Benefiting from the alignment-refinement
strategy, FIA-Flow significantly outperforms state-of-theart methods, especially in recovering details across diverse
architectures and layers. FIA-Flow’s effectiveness and data
efficiency demonstrate that Split DNNs face a more severe and practical privacy threat than previously recognized.
These findings underscore the urgent need for designing robust and efficient defense mechanisms that can mitigate privacy risks while preserving model utility and inference performance.


**References**


[1] Nilesh Ahuja, Parual Datta, Bhavya Kanzariya, V Srinivasa
Somayazulu, and Omesh Tickoo. Neural rate estimator and
unsupervised learning for efficient distributed image analytics in split-DNN models. In _IEEE Conf. Comput. Vis. Pattern_
_Recog._, pages 2022–2030, 2023. 2

[2] Dake Chen, Shiduo Li, Yuke Zhang, Chenghao Li, Souvik
Kundu, and Peter A Beerel. DIA: Diffusion based inverse
network attack on collaborative inference. In _IEEE Conf._
_Comput. Vis. Pattern Recog. Worksh._, pages 124–130, 2024.
2

[3] Li Chen, Penghao Wu, Kashyap Chitta, Bernhard Jaeger, Andreas Geiger, and Hongyang Li. End-to-end autonomous
driving: Challenges and frontiers. _IEEE Trans. Pattern Anal._
_Mach. Intell._, 2024. 1

[4] Jia Deng, Wei Dong, Richard Socher, Li-Jia Li, Kai Li,
and Li Fei-Fei. ImageNet: A large-scale hierarchical image
database. In _IEEE Conf. Comput. Vis. Pattern Recog._, pages
248–255, 2009. 4

[5] Ulyanov Dmitry, Andrea Vedaldi, and Lempitsky Victor.
Deep image prior. _Int. J. Comput. Vis._, 128(7):1867–1888,
2020. 2, 5

[6] Carl Doersch. Tutorial on variational autoencoders. _arXiv_
_preprint arXiv:1606.05908_, 2016. 3

[7] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun.
Deep residual learning for image recognition. In _IEEE Conf._
_Comput. Vis. Pattern Recog._, pages 770–778, 2016. 5

[8] Lijun He, Zhihan Ren, Wanyue Zhang, Fan Li, and Shaohui Mei. Unsupervised pansharpening based on double-cycle
consistency. _IEEE Transactions on Geoscience and Remote_
_Sensing_, 62:1–15, 2024. 1

[9] Jonathan Ho, Ajay Jain, and Pieter Abbeel. Denoising diffusion probabilistic models. In _Adv. Neural Inform. Process._
_Syst._, pages 6840–6851, 2020. 8

[10] Edward J. Hu, Yelong Shen, Phillip Wallis, Zeyuan AllenZhu, Yuanzhi Li, Shean Wang, Lu Wang, and Weizhu Chen.
LoRA: Low-Rank Adaptation of Large Language Models. In
_Int. Conf. Learn. Represent._, 2022. 5

[11] Glenn Jocher and Jing Qiu. Ultralytics yolo11, 2024. 5

[12] Mostafa Kahla, Si Chen, Hoang Anh Just, and Ruoxi Jia.
Label-only model inversion attacks via boundary repulsion.
In _IEEE Conf. Comput. Vis. Pattern Recog._, pages 15045–
15053, 2022. 2

[13] Yiping Kang, Johann Hauswald, Cao Gao, Austin Rovinski,
Trevor Mudge, Jason Mars, and Lingjia Tang. Neurosurgeon: Collaborative intelligence between the cloud and mobile edge. _ACM SIGARCH Computer Architecture News_, 45
(1):615–629, 2017. 1, 2

[14] Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B
Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec
Radford, Jeffrey Wu, and Dario Amodei. Scaling laws for
neural language models. _arXiv preprint arXiv:2001.08361_,
2020. 1

[15] Jyotirmoy Karjee, Praveen Naik, Kartik Anand, and Vanamala N Bhargav. Split computing: Dnn inference partition
with load balancing in iot-edge platform for beyond 5g. _Mea-_
_surement: Sensors_, 23:100409, 2022. 2




[16] Tero Karras, Samuli Laine, and Timo Aila. A style-based
generator architecture for generative adversarial networks. In
_IEEE Conf. Comput. Vis. Pattern Recog._, pages 4401–4410,
2019. 2

[17] Tero Karras, Samuli Laine, Miika Aittala, Janne Hellsten,
Jaakko Lehtinen, and Timo Aila. Analyzing and improving
the image quality of stylegan. In _IEEE Conf. Comput. Vis._
_Pattern Recog._, pages 8110–8119, 2020. 2

[18] Diederik P Kingma and Max Welling. Auto-Encoding Variational Bayes. _arXiv preprint arXiv:1312.6114_, 2013. 2

[19] Alex Krizhevsky, Ilya Sutskever, and Geoffrey E Hinton.
Imagenet classification with deep convolutional neural networks. _Communications of the ACM_, 60(6):84–90, 2017. 5

[20] Wa-Kin Lei, Jun-Cheng Chen, and Shang-Tse Chen. DRAG:
Data reconstruction attack using guided diffusion. _arXiv_
_preprint arXiv:2509.11724_, 2025. 2

[21] Dawei Li, Xiaolong Wang, and Deguang Kong. Deeprebirth:
Accelerating deep neural network execution on mobile devices. In _AAAI_, 2018. 1

[22] Haoyang Li, Li Bai, Qingqing Ye, Haibo Hu, Yaxin Xiao,
Huadi Zheng, and Jianliang Xu. A sample-level evaluation
and generative framework for model inversion attacks. In
_AAAI_, pages 18287–18295, 2025. 2

[23] Ziang Li, Hongguang Zhang, Juan Wang, Meihui Chen,
Hongxin Hu, Wenzhe Yi, Xiaoyang Xu, Mengda Yang, and
Chenjun Ma. From head to tail: Efficient black-box model
inversion attack via long-tailed learning. In _IEEE Conf. Com-_
_put. Vis. Pattern Recog._, pages 29288–29298, 2025. 2

[24] Shijun Liang, Evan Bell, Qing Qu, Rongrong Wang, and
Saiprasad Ravishankar. Analysis of deep image prior and exploiting self-guidance for image reconstruction. _IEEE Trans-_
_actions on Computational Imaging_, 2025. 2, 5

[25] Tsung-Yi Lin, Michael Maire, Serge Belongie, James Hays,
Pietro Perona, Deva Ramanan, Piotr Doll´ar, and C Lawrence
Zitnick. Microsoft coco: Common objects in context. In _Eur._
_Conf. Comput. Vis._, pages 740–755. Springer, 2014. 6

[26] Yaron Lipman, Ricky TQ Chen, Heli Ben-Hamu, Maximilian Nickel, and Matt Le. Flow matching for generative modeling. _arXiv preprint arXiv:2210.02747_, 2022. 2

[27] Hao Liu, Lijun He, Miao Zhang, and Fan Li. Vadiffusion:
Compressed domain information guided conditional diffusion for video anomaly detection. _IEEE Trans. Circuit Syst._
_Video Technol._, 34(9):8398–8411, 2024. 1

[28] Hao Liu, Lijun He, Jiaxi Liang, Zhihan Ren, and Fan Li.
Dependency structure augmented contextual scoping framework for multimodal aspect-based sentiment analysis. _arXiv_
_preprint arXiv:2504.11331_, 2025. 1

[29] Xingchao Liu, Chengyue Gong, and Qiang Liu. Flow
straight and fast: Learning to generate and transfer data with
rectified flow. _arXiv preprint arXiv:2209.03003_, 2022. 2

[30] Yufan Liu, Wanqian Zhang, Dayan Wu, Zheng Lin, Jingzi
Gu, and Weiping Wang. Prediction exposes your face:
Black-box model inversion via prediction alignment. In _Eur._
_Conf. Comput. Vis._, pages 288–306. Springer, 2024. 2

[31] Ze Liu, Yutong Lin, Yue Cao, Han Hu, Yixuan Wei, Zheng
Zhang, Stephen Lin, and Baining Guo. Swin transformer:
Hierarchical vision transformer using shifted windows. In
_Int. Conf. Comput. Vis._, pages 10012–10022, 2021. 5


[32] Aravindh Mahendran and Andrea Vedaldi. Understanding
deep image representations by inverting them. In _IEEE Conf._
_Comput. Vis. Pattern Recog._, pages 5188–5196, 2015. 2, 5

[33] Anish Mittal, Rajiv Soundararajan, and Alan C Bovik. Making a “completely blind” image quality analyzer. _IEEE Sign._
_Process. Letters_, 20(3):209–212, 2012. 5

[34] Waleed Hassan Mubark, Jagannath Guptha Kasula, and
Md Yusuf Sarwar Uddin. Asap: Asynchronous split inference for accelerated dnn execution. In _Proceedings of_
_the 25th International Conference on Distributed Computing_
_and Networking_, pages 32–44, 2024. 2

[35] Maxime Oquab, Timoth´ee Darcet, Th´eo Moutakanni, Huy
Vo, Marc Szafraniec, Vasil Khalidov, Pierre Fernandez,
Daniel Haziza, Francisco Massa, Alaaeldin El-Nouby, et al.
DINOv2: Learning robust visual features without supervision. _arXiv preprint arXiv:2304.07193_, 2023. 5

[36] Guansong Pang, Chunhua Shen, Longbing Cao, and Anton
Van Den Hengel. Deep learning for anomaly detection: A
review. _ACM Computing Surveys (CSUR)_, 54(2):1–38, 2021.
1

[37] Tianwen Qian, Jingjing Chen, Linhai Zhuo, Yang Jiao, and
Yu-Gang Jiang. NuScenes-QA: A Multi-Modal Visual Question Answering Benchmark for Autonomous Driving Scenario. In _AAAI_, pages 4542–4550, 2024. 1

[38] Shaoqing Ren, Kaiming He, Ross Girshick, and Jian Sun.
Faster R-CNN: Towards real-time object detection with region proposal networks. _IEEE Trans. Pattern Anal. Mach._
_Intell._, 39(6):1137–1149, 2016. 7

[39] Zhihan Ren, Lijun He, and Jichuan Lu. Context aware edgeenhanced gan for remote sensing image super-resolution.
_IEEE Journal of Selected Topics in Applied Earth Observa-_
_tions and Remote Sensing_, 17:1363–1376, 2023. 1

[40] Renan A Rojas-Gomez, Raymond A Yeh, Minh N Do, and
Anh Nguyen. Inverting adversarially robust networks for image synthesis. In _ACCV_, pages 2221–2238, 2022. 2, 5

[41] Robin Rombach, Andreas Blattmann, Dominik Lorenz,
Patrick Esser, and Bj¨orn Ommer. High-resolution image synthesis with latent diffusion models. In _IEEE Conf. Comput._
_Vis. Pattern Recog._, pages 10684–10695, 2022. 5

[42] Muhammad Shiraz, Abdullah Gani, Rashid Hafeez Khokhar,
and Rajkumar Buyya. A review on distributed application
processing frameworks in smart mobile devices for mobile
cloud computing. _IEEE Communications Surveys & Tutori-_
_als_, 15(3):1294–1313, 2012. 1

[43] Abhishek Singh, Ayush Chopra, Ethan Garza, Emily Zhang,
Praneeth Vepakomma, Vivek Sharma, and Ramesh Raskar.
Disco: Dynamic and invariant sensitive channel obfuscation
for deep neural networks. In _IEEE Conf. Comput. Vis. Pat-_
_tern Recog._, pages 12125–12135, 2021. 6, 7

[44] Surat Teerapittayanon, Bradley McDanel, and Hsiang-Tsung
Kung. Branchynet: Fast inference via early exiting from
deep neural networks. In _Int. Conf. Pattern Recog._, pages
2464–2469. IEEE, 2016. 2

[45] Surat Teerapittayanon, Bradley McDanel, and Hsiang-Tsung
Kung. Distributed deep neural networks over the cloud, the
edge and end devices. In _2017 IEEE 37th international con-_
_ference on distributed computing systems (ICDCS)_, pages
328–339. IEEE, 2017. 1




[46] Tom Titcombe, Adam J Hall, Pavlos Papadopoulos, and
Daniele Romanini. Practical defences against model inversion attacks for split neural networks. _arXiv preprint_
_arXiv:2104.05743_, 2021. 6, 7

[47] Praneeth Vepakomma, Abhishek Singh, Otkrist Gupta, and
Ramesh Raskar. Nopeek: Information leakage reduction to
share activations in distributed deep learning. In _2020 Inter-_
_national Conference on Data Mining Workshops (ICDMW)_,
pages 933–942. IEEE, 2020. 6

[48] Ruofeng Yang, Bo Jiang, Cheng Chen, Ruinan Jin, Baoxiang Wang, and Shuai Li. Few-shot diffusion models escape
the curse of dimensionality. In _Adv. Neural Inform. Process._
_Syst._, pages 68528–68558. Curran Associates, Inc., 2024. 3

[49] Sidi Yang, Tianhe Wu, Shuwei Shi, Shanshan Lao, Yuan
Gong, Mingdeng Cao, Jiahao Wang, and Yujiu Yang.
MANIQA: Multi-dimension attention network for noreference image quality assessment. In _IEEE Conf. Comput._
_Vis. Pattern Recog._, pages 1191–1200, 2022. 5

[50] Zipeng Ye, Wenjian Luo, Muhammad Luqman Naseem, Xiangkai Yang, Yuhui Shi, and Yan Jia. C2fmi: Corse-to-fine
black-box model inversion attack. _IEEE Transactions on De-_
_pendable and Secure Computing_, 21(3):1437–1450, 2023. 2

[51] Jason Yosinski, Jeff Clune, Yoshua Bengio, and Hod Lipson.
How transferable are features in deep neural networks? _Adv._
_Neural Inform. Process. Syst._, 27, 2014. 3

[52] Richard Zhang, Phillip Isola, Alexei A Efros, Eli Shechtman,
and Oliver Wang. The unreasonable effectiveness of deep
features as a perceptual metric. In _IEEE Conf. Comput. Vis._
_Pattern Recog._, pages 586–595, 2018. 4, 5

[53] Sai Qian Zhang, Ziyun Li, Chuan Guo, Saeed Mahloujifar, Deeksha Dangwal, Edward Suh, Barbara De Salvo, and
Chiao Liu. Unlocking visual secrets: Inverting features with
diffusion priors for image reconstruction. _arXiv preprint_
_arXiv:2412.10448_, 2024. 2

[54] Tianyi Zhang, Varsha Kishore, Felix Wu, Kilian Q Weinberger, and Yoav Artzi. BERTScore: Evaluating text generation with bert. _arXiv preprint arXiv:1904.09675_, 2019.
5

[55] Zhanke Zhou, Jianing Zhu, Fengfei Yu, Xuan Li, Xiong
Peng, Tongliang Liu, and Bo Han. Model inversion attacks:
A survey of approaches and countermeasures. _arXiv preprint_
_arXiv:2411.10023_, 2024. 2

[56] Yixuan Zhu, Wenliang Zhao, Ao Li, Yansong Tang, Jie
Zhou, and Jiwen Lu. Flowie: Efficient image enhancement via rectified flow. In _IEEE Conf. Comput. Vis. Pattern_
_Recog._, pages 13–22, 2024. 2


