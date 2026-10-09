# Historical PhysX receipt index / 历史 PhysX 回执索引

[English audit](physx-solver-audit.md) · [中文审计](physx-solver-audit.zh-CN.md) · [Open gaps / 剩余缺口 #126](https://github.com/huangkiki/Dexlab/issues/126)

2026-10-09: 145 logical entries, including reused records, failed admissions and intermediate states; not independent successful trials. / 共 145 条逻辑记录，含复用、准入失败和中间状态，不是独立成功试验数。

Receipt hashes identify the exact archived JSON; they do not attest loaded PhysX libraries. `completed` is a recorder state, not a score. Paths below are archive/repository-relative identities, not local deployment locations. / 回执哈希标识原始 JSON，不证明加载库身份；完成状态不等于验收通过，以下为归档内或仓库内标识。

Package codes / 包清单：**H** = Isaac Sim 5.1.0.0, IsaacLab 0.47.2, Torch 2.7.0+cu128; **K** also records / 另记录 isaacsim-kernel 5.1.0.0; **—** = absent in receipt / 回执未记录。Adapter version and native core identity remain separate; no row supplies the missing loaded-core attestation. / 适配器版本与核心身份分开；所有条目仍缺同期加载核心证明。

## contact-details-v1

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `contact-details-v1/run.json` | completed | — | `529c8d1ec69ef2cbe9f98fd6a87a540a72c8788d01720712e29392572feaafd3` |

## drive-v1

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `drive-v1/native-drive-comparison-v1/pgs/run.json` | completed | H | `61f9ad88ba0edbf9e903fd4caa9e536e744e6f35d45878fa8863c1c7ff540bc8` |
| `drive-v1/native-drive-comparison-v1/tgs-default/run.json` | completed | H | `668a42524c75d39d4df3de02df168214511e56ccef897a42b52e0a24cec91ec6` |
| `drive-v1/native-drive-comparison-v1/tgs-substep/run.json` | completed | H | `25f5b5ba6057d737d684a6a75600cfaf97bfb20c3d857027d2b784d64611a5d1` |
| `drive-v1/native-drive-direct-v1/run.json` | completed | H | `811331670e17eca0fffb8a12bcfd219a48a4e5f7ad9761aebb9da34ee8ffe635` |
| `drive-v1/native-drive-direct-v2/run.json` | completed | H | `6c4dc716b9c129e06173fc3512a8ec735ab993016c9798a7c95223958cfb0ca2` |
| `drive-v1/qualification/baseline-rest/run.json` | completed | H+K | `ed9d60c92fc30d3b14253e55fff520f0c77102ddc250c18c64cd3007964a62e0` |
| `drive-v1/qualification/baseline-slide/run.json` | completed | H+K | `7a52383cc5b5e2e329da110d942612af229ff8d3f6e22bc419b22c447c7bea1e` |
| `drive-v1/qualification/baseline-slide-frictionless/run.json` | completed | H+K | `cdb41c8099e67c8e4728d91a4bcf9474efe385a148ac349d6bfa7fbefea9a2e8` |
| `drive-v1/qualification/default/run.json` | completed | H+K | `9e2523fcc2cb884f8d67e46f6afd0c82d68f44ba445c253e80bd36931fe1d135` |
| `drive-v1/qualification/pinch-frictionless/run.json` | completed | H+K | `64b02ae82e96443c7f2233c4e1f05a59628cc1da5ec9f8ea8785d5c33393a947` |
| `drive-v1/qualification/pinch-hold/run.json` | completed | H+K | `9828580e0922370026e2da528b81c645826f6d29c265063c4483ec9639708526` |
| `drive-v1/qualification/pinch-overload/run.json` | completed | H+K | `855788f30aa662e8190bde4605a23ed10d819bbdc5f86306a82d9d9285dc256e` |
| `drive-v1/qualification/substep/run.json` | completed | H+K | `7d61074545d96719179081e0f10e0ea85f6065da48fe5d37e94befbcc09aed73` |

## pinch-v2

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `pinch-v2/qualification-v1/frictionless/run.json` | completed | H+K | `df5ff0ae8776bbe5b50439d09ed5fd36d6f162f30238e3a0bb947dc01538dde8` |
| `pinch-v2/qualification-v1/hold/run.json` | completed | H+K | `5a4a7c59b03be6282cf0504b17491419c7ee1ff99ba5b0cb975b9bc475209c67` |
| `pinch-v2/qualification-v1/overload/run.json` | completed | H+K | `36d25f542e8f53d16a4442a007c315394bc6e20904874b8222cea5bc6e91ff1b` |
| `pinch-v2/qualification-v2/frictionless/run.json` | completed | H+K | `3dd5fe543c5fbebc9d129e7116d38955f9d2dbdf19b25156e4daab2b72a5386d` |
| `pinch-v2/qualification-v2/hold/run.json` | completed | H+K | `b1259e59521a01c85e2c94a07344cea539e700bd67918a72bde2479f4c606879` |
| `pinch-v2/qualification-v2/overload/run.json` | completed | H+K | `58a909797bb05a6e407bc92fbe7ffa87f992510ebd8b6ba8ce3ce896cdddebe0` |
| `pinch-v2/unsupported-passive-damping/run.json` | error | — | `3562c9dfc8d29cf9ffe105e159d4dbf7bf9e6f7f13b7c9d8529ae4f2ca8d30fb` |

## qualification-v1

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `qualification-v1/original-adapter-failures/rest-v1/run.json` | error | H+K | `0a15a93c1972537cf07f71887fb62e900ff7d35d9f9cda633ffedd25dc3ecf81` |
| `qualification-v1/original-adapter-failures/rest-v2/run.json` | error | H+K | `93a84cde95d5672b909d904b5a2a52339156b4a7f0030df698fa54c5563e40d3` |
| `qualification-v1/rest/run.json` | completed | H+K | `04956d78675b4313f3635dc22388fcb1e0c2d69cf7b4af0a699abcf23a306bcd` |
| `qualification-v1/slide/run.json` | completed | H+K | `fbaf502c45f3195dc7807637728ca17fa7725b1f391e262d1e5b0f13d1ba312c` |
| `qualification-v1/slide-frictionless/run.json` | completed | H+K | `f0ea2b0f9152d488851def9b087a36e39409c781c1b1939ffd4d788a75f1d295` |

## v0.7.0

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `robot-v1/robot-articulation-final-v1/run.json` | completed | H+K | `510d54c1ba035c3c8e02a2cd4d502d6c5a2b06a0361be7002b200ff92208c7f4` |
| `robot-v1/robot-articulation-qualification-v1/run.json` | completed | — | `6978df1385e851677f255f52b1a26000ace7532683c02ea436980f941eb2f29d` |
| `robot-v1/robot-articulation-qualification-v2/run.json` | completed | — | `b456fb6a4c11e59db9a626e12089b8070d1839cb72236a63eeb017e0c21b876b` |
| `robot-v1/robot-articulation-qualification-v3/run.json` | completed | H+K | `103bd61f582aa411e60fc19ebbf9d53db74cc9e0224e0862978462946f73810a` |
| `robot-v1/robot-articulation-qualification-v4/run.json` | completed | H+K | `eb49abd217494ddd5ec5a4e30f23a26a6586cb6805fb74f0968265eea26ac5f1` |
| `robot-v1/robot-articulation-v1/run.json` | completed | — | `4e154441a4ce4d8ccd27947a34e994bbbdff0796b4b585796464b0ed1bd4af83` |
| `robot-v1/robot-import-v1/run.json` | rejected | — | `a28ee04c45214dd7bcdf747cc0da8dc82bfa91e04ded98e755d32468e9e90ace` |
| `robot-v1/robot-import-v2/run.json` | rejected | — | `7ff3333a658fafe3b5c124bae78448dbf50b1ff2b2900806ff2a915aa0e76376` |
| `robot-v1/robot-import-v3/run.json` | imported | — | `2b3608a0dade866cdd8a6e77f3f8e98c995969ccbe90e679763804a35719feb4` |

## v0.8.0

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `sdf-v1/convex-hole-dev-v1/run.json` | completed | — | `e3e4e021ecbb649867a5a20526b5ddda6306612d8b14277c58c5b3c27a759425` |
| `sdf-v1/robot-sdf-import-v1/run.json` | completed | — | `6f8d7998b83465d204770724dbc5505ddc4e513e9d150bc35b264d886ead0996` |
| `sdf-v1/sdf-hole-dev-v1/run.json` | error | — | `260a1ed6bdf1062e4492988929aac3dce9d77e095822fe0208264d8c1cfced73` |
| `sdf-v1/sdf-hole-dev-v2/run.json` | error | — | `7658423f1506f2be9525c90e341bc987760b50f6b8f960100ed5faad061c4707` |
| `sdf-v1/sdf-hole-dev-v3/run.json` | completed | — | `d6972a0c8db7391843dec247dd53c57cb349d4d74bcd0d1403a8dca2c0db143c` |
| `sdf-v1/sdf-mesh-refinement-v1/run.json` | completed | H+K | `7f14a72f0890ea5e14febe056ff3fa626642702a6ab1331d4d2d126faaf88664` |
| `sdf-v1/sdf-qualification-v1/convex-hole/run.json` | completed | H+K | `e9c53947dcd0f543b37125e476eea14ca44e7567c2fec34843328bf5cb8ef712` |
| `sdf-v1/sdf-qualification-v1/sdf-hole/run.json` | completed | H+K | `589ed13bcc3cb185d03de1f95b6cd82eee88f89b67641f10ed6bff11e1e7fdf9` |
| `sdf-v1/sdf-qualification-v1/sdf-surface/run.json` | completed | H+K | `12f2fc85f400b85fdaf9d83b3f1a3b2949422663e2e9b2040cfe07ce6cfa8448` |
| `sdf-v1/sdf-qualification-v2/convex-hole/run.json` | completed | H+K | `1652dda6b025089b6d07f7879e7b468118cae269d842d8dded5789d8fcb8b4cf` |
| `sdf-v1/sdf-qualification-v2/sdf-hole/run.json` | completed | H+K | `8b8e52f65479a1088b2bbe72e6b577dc63b4ab33d9fff92f8887e2c195ee4206` |
| `sdf-v1/sdf-qualification-v2/sdf-surface/run.json` | completed | H+K | `a5f88ea5e69febe8338976009f3a0a1334026754f7a55f2e6e8ee75406548531` |
| `sdf-v1/sdf-qualification-v3/convex-hole/run.json` | completed | H+K | `ebc4347398f258c57c1ca114951c099a44ad01adf58dd46999ddc047c8f7be60` |
| `sdf-v1/sdf-qualification-v3/sdf-hole/run.json` | completed | H+K | `433b685024adb38f9c2396dfcc5826e5ccaa7919908623a91122c3f53bb0b5b3` |
| `sdf-v1/sdf-qualification-v3/sdf-surface/run.json` | completed | H+K | `30ee0b4264f5b39b15f5da83d9ce10813e06053166ffa5be962c9e0bd366678a` |
| `sdf-v1/sdf-surface-dev-v1/run.json` | completed | — | `b95b2788e436789f9df032b545f3e60ad1ffdc3273e3b028b47fdc0ae5a19a8d` |

## v0.11.0

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `demos/physx-contact/runs/cloth-development-final-v2/dev-drape-physx-surface/run.json` | completed | H | `25e33038032fe611d3c1738f40be016f1a6cdbf89501a72fcb98b0c761ebb2aa` |
| `demos/physx-contact/runs/cloth-development-final-v2/dev-extension-physx-surface/run.json` | unsupported | — | `2deaf1f1398f54ba60a705fbbd43644f71d499046a9bc558256bfb49dc5720b5` |
| `demos/physx-contact/runs/cloth-development-final-v2/dev-folded-drop-physx-surface/run.json` | completed | H | `8cf8eadf518eaafc6c5608fc2f81bc23ec22e363d2ca0f9d175db22d48c743d6` |
| `demos/physx-contact/runs/cloth-development-final-v2/dev-sag-physx-surface/run.json` | completed | H | `aed76f42b4a2f530e771ff02e40b6f753e53a9ae539dacef11526a86178c0af0` |
| `demos/physx-contact/runs/cloth-development-v1/dev-drape-physx-surface/run.json` | completed | H | `b84adea5d4995903659785342c6e3d8cf13ccb7c14685df4c5e07c1f32f02103` |
| `demos/physx-contact/runs/cloth-development-v1/dev-extension-physx-surface/run.json` | unsupported | — | `98ff92e4d8ef84561ba69611890608ffaf7040a526e35874d34d9fed5d98b1a3` |
| `demos/physx-contact/runs/cloth-development-v1/dev-folded-drop-physx-surface/run.json` | completed | H | `ef4aa057fae6c5266387f9e2a0658b3e2a515624b3a61ee3218690afaab31dc5` |
| `demos/physx-contact/runs/cloth-development-v1/dev-sag-physx-surface/run.json` | completed | H | `b48b58b44173f9cd6daba48b12b5361227732134d52408492162759a761489a0` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-drape-00-physx-surface/run.json` | completed | H | `323f0d16351e5a003efae230f2982f62ac851228e98dd4bbf31a90680cf8366b` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-drape-01-physx-surface/run.json` | completed | H | `dd50f201acb408cfb0f9da37599d1c369dea75f7a0cbca48fb3fc2dc9c3ce311` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-drape-02-physx-surface/run.json` | completed | H | `80e8bcfbc53674fe8669269a8d414694d9d80dd195b8b2b6321b3d7875dcb8c0` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-drape-03-physx-surface/run.json` | completed | H | `bcc3354dc585f64ac3649f19b83a29dd284bc36d3235948c6bd2a4f8934b63ee` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-extension-00-physx-surface/run.json` | unsupported | — | `a5eeb92813eb2854147faf715a4e1893eff003c4c1822d7fd0b95edccc2ea886` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-extension-01-physx-surface/run.json` | unsupported | — | `95a724e863aa31afeefc2d107ee126fb2203c896711914f28e3bd311e6d93501` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-extension-02-physx-surface/run.json` | unsupported | — | `bec4509214a7b1706cf221c3196a48805d46299000fcb920a70f61195657e5fa` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-extension-03-physx-surface/run.json` | unsupported | — | `3a7cae0a2d3f2636699163491ad9033c47377f922c417a73938f8dea105699f7` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-folded-drop-00-physx-surface/run.json` | completed | H | `b77e43662643685227abca42a713f7f706a94e8bf743799e992dfdf5a15b92d7` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-folded-drop-01-physx-surface/run.json` | completed | H | `4759b5150fb3fb987d3dbce09e16fb2d4237cbd8cd8836b4e5ab8d845a5932d3` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-folded-drop-02-physx-surface/run.json` | completed | H | `b3e10c1669f45fbd1d604e649d393c0c693424373cdd16ccd0034fb65df818e2` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-sag-00-physx-surface/run.json` | completed | H | `9825e0f33d35b8ce4a73e8ebaa9f460e87e38ed7601a6b40fc540cee465396c9` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-sag-01-physx-surface/run.json` | completed | H | `3f1de627d5ac88f0200c1edc1fa057bbfb0c217fe6645378d8a4e29d19086e4d` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-sag-02-physx-surface/run.json` | completed | H | `9b12c1b22bcfb2e205bdee83a6bf8c49ec401b5a1c387206fd352c754a5b902e` |
| `demos/physx-contact/runs/cloth-heldout-v1/test-sag-03-physx-surface/run.json` | completed | H | `e227df8724f3a490147b1901a8622ce9230e36dd9e5caa34abe06c018519670c` |
| `demos/physx-contact/runs/cloth-public-sag-v2/run.json` | completed | H | `eed5440fa3bfaf4333b098d62bed9847f80af58831c2da4a810ea9290315352f` |
| `demos/physx-contact/runs/cloth-public-sag-v3/run.json` | completed | H | `2ed1369d5c0f6b4ac1a9ed0db1c3a3dceb4abc37f3f1ac0c4ef6b0b69b22ad12` |
| `demos/physx-contact/runs/cloth-public-sag-v4/run.json` | completed | H | `fb57bf9e8ec30b5943c0bde020fe5bd87ac57c063fb7e57b11112cffed7e2d11` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-drape-125us/run.json` | completed | H | `9cb51b9130e125b9dd0315f348a634d34f6dc2aead9e25748cb153d56beaef17` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-drape-250us/run.json` | completed | H | `069cb115d3817f140a3df7a8da1f58599ca1933c45b08c11bef20724bdf42d60` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-drape-refined/run.json` | completed | H | `b3a4bdb80e81d96a88abbbd81502ce0e2dcc91d06b7fc08d457879e58b66974c` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-folded-drop-125us/run.json` | completed | H | `1d46583e87de557a8d756f8e5eae968a6995ee9c7430c2a9730bc54be0307c56` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-folded-drop-250us/run.json` | completed | H | `70059690789b25be71a886903dcef982b456e482614c542c1d03dc69dd7aa7cc` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-folded-drop-refined/run.json` | completed | H | `f4b71bcc6d88011d58fe35ad6e58b8d11117a78bc4d7305c0f026926e6ebd3a5` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-sag-125us/run.json` | completed | H | `cf898e61c61e8ba06b733a79ebc6a82e6483f369cc9f4f93a4892e74eaceaac8` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-sag-250us/run.json` | completed | H | `88a9d0e9aac4c5c57b3cf67fac30ef3dd06e6498aa7f697de818afe419e30338` |
| `demos/physx-contact/runs/cloth-refinement-v1/dev-sag-refined/run.json` | completed | H | `824fd0a38224ead1373edb7c21a57524a12cdb2e1b2818a9791543639e3375e4` |
| `demos/physx-contact/runs/cloth-sag-probe-v1/run.json` | preparing | — | `01bb7e563115922d29b85a37a22f389eb708f176d19531d0666ce8587b6c5ca6` |
| `demos/physx-contact/runs/cloth-sag-probe-v3/run.json` | running | — | `18b991779565b12054fe039662f3599516aa29d2281999cf3c0cb32e375540f0` |
| `demos/physx-contact/runs/cloth-sag-probe-v4/run.json` | completed | — | `f790b9bb9793bf95849cef57a518079d3c3750cea524f76ee8df0e632f46a264` |
| `demos/physx-contact/runs/cloth-sag-probe-v5/run.json` | completed | — | `511feeca1bca7fa70e288897138dd1f855e29abf99acd5e6c86f1e3377db2d46` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-drape-00-physx-surface/run.json` | completed | H | `97f4f79d3a8eb64f3c5ac6bd30b150f5d8a2091b74fa7e5628195aa543e2a23d` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-drape-01-physx-surface/run.json` | completed | H | `c3482c85bb8918a0e9d6585cf918642b412dd4ee301d1696db3450ca1f87aa37` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-drape-02-physx-surface/run.json` | completed | H | `d98940fa548bb235cfce87167428d9932469223201ddbf6c8ad14060e622661a` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-drape-03-physx-surface/run.json` | completed | H | `baa6648946be9a097e8e04e093e36876a40e9e68cdd27112de52c74b3f07bfec` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-extension-00-physx-surface/run.json` | unsupported | — | `537d59ffd494d868758e8284982ffb358c5fb711256009a705d2b71ff3ca6251` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-extension-01-physx-surface/run.json` | unsupported | — | `6c95b238f3295aaac7eea2182a5604391a63af72674cc643490fb967a48a78d8` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-extension-02-physx-surface/run.json` | unsupported | — | `4a7d5d09446064839422d9dcea1152d6fd101fe25a37e1219b2c232bb8fca49a` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-extension-03-physx-surface/run.json` | unsupported | — | `9f2f6655141ebccf01c86ac47aac32acf12dd5dc53fa9d23f4ad8a8163c5c6fd` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-folded-drop-00-physx-surface/run.json` | completed | H | `8e9419d4b744f4412cf98fac2e937c4163fef10bf91d6b177d7b0dfc77d87c28` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-folded-drop-01-physx-surface/run.json` | completed | H | `78b898a1fd1f5fc0dff42d9930eb16a8d78f6e89433b14668648f5279cf599d3` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-folded-drop-02-physx-surface/run.json` | completed | H | `cdc13b27c95b259be30177eac8c7f4ffe6af39bcde0c6777486b4c208d855cbc` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-sag-00-physx-surface/run.json` | completed | H | `b36adb677aac2b20a42a89139c8a8035263520f4f38e7b89af82540800a2bae4` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-sag-01-physx-surface/run.json` | completed | H | `8d6ce0e8965d2cd2d11326350ffabb0f037b4ec201b726f1de1dadd11a5d04a8` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-sag-02-physx-surface/run.json` | completed | H | `108e181f9906efc6d1fd0ff3a9b80ef0aa004350f9537f6a8eb732a98758cffb` |
| `demos/physx-contact/runs/cloth-test-final-v2/test-sag-03-physx-surface/run.json` | completed | H | `0129ba1df38cf9169f06546609756c8aeda8d1840372850685c656ad48663cbe` |

## v0.12.0

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `admission/cylinder-physx-v1/run.json` | error | — | `0ca84e66002fbb5fc714d3011c930166eda289bb570e84f9647439094031aca7` |
| `raw/cylinder-development-v1/physx-dev-cylinder-frictionless/run.json` | completed | H+K | `cb8ea4c46843df7268c0f58a274633814b2ae66fa9d1ea9a5019f6e5646bf73c` |
| `raw/cylinder-development-v1/physx-dev-cylinder-hold/run.json` | completed | H+K | `b6305f851193a02e1eb36269257f29ba9981a9cf0df3bce99a27d1f52453ed50` |
| `raw/cylinder-development-v1/physx-dev-cylinder-overload/run.json` | completed | H+K | `906dbe1399f1b2311f3748a7ead930cb488241f91fac0ebe7220347da4daea30` |
| `raw/cylinder-development-v1/physx-dev-cylinder-ramp/run.json` | completed | H+K | `387ca78f47bf5d63b432dbb431d4f90424bd16a37a01b83e0f52bba6d3440c2a` |
| `raw/indent-physx-v1/run.json` | completed | H+K | `29d9d345f4848901cc049177736399405613db08316c332f779b572db7168293` |
| `raw/plane-development-v1/physx-dev-frictionless/run.json` | completed | H+K | `4bab216c9668ba822d42847c1271777a7f7189ccdea7955b126dee315c1d4200` |
| `raw/plane-development-v1/physx-dev-rest/run.json` | completed | H+K | `5e59ed55d4f1f29c8d6e8cd9e5c6feafcc03d984b94ca1d305c5d3becc13e10c` |
| `raw/plane-development-v1/physx-dev-slide/run.json` | completed | H+K | `e0039de977a4764e5d0ab10dc59697e63876c1bd4a349cce29ef17476f305f54` |
| `raw/plane-development-v1/physx-dev-slide-reverse/run.json` | completed | H+K | `c24415802a8f307102b1f06e1bc2e87e79cac877e0ceb3ec215e8ad827a39467` |

## v0.13.0

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `raw/initial-physx/run.json` | completed | H+K | `aeec0930c58ba26d2bfea5fbed5014126badf4b8303f8f0d74200d446c7c02b7` |
| `raw/validation-physx-h2/run.json` | completed | H+K | `ca370026ead516ff6f7b6e88beefa4d040a07b879e9bc13e55f2f4d43364ce31` |
| `raw/validation-physx-mass01/run.json` | completed | H+K | `b5cea49b05991cecc621eee9fea6dd72ed0fee6525247869a752ba737c75a8d9` |
| `raw/validation-physx-mass04/run.json` | completed | H+K | `9acc86fbaed25fa3d4a48a799a729033907aae80509093c434b3fad0ce230fc9` |
| `raw/validation-physx-reference/run.json` | completed | H+K | `eb1fd1d4bfdbedb8d5a55d3db2f016c6757109dd25ae322982722b679043ba93` |

## v0.14.0

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `inertia-repeat/run.json` | completed | H+K | `ef6abf3f9f6f17228b134135df284a57879ed8e1e9f79c052ff09361160764f2` |
| `raw/physx-force-spring-125us/run.json` | completed | H+K | `39f85c2140d16570258559925a4a73bbf812a2c312372212874ec6dfedf266ab` |
| `raw/physx-force-spring-250us/run.json` | completed | H+K | `c057a4ac18efa97d30dbf9fa99e0f069e9b8a77bae5459a720be9e6115676e89` |
| `raw/physx-force-spring-500us/run.json` | completed | H+K | `8f2024ce122ad631a2273800bcee801c6ecd9fd5f82887d31bc91fa7d3143539` |

## apple-grasp-v1

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `apple-public-final-v1/run.json` | completed | H+K | `16f9f76164aaf323041ee71d9c417b934293688d2838def19f6b1b081051768a` |

## apple-development-v1.json

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `apple-sdf-dev-v1/run.json` | error | — | `467a747f9f239bede859717249cf609270188d14307e6da6d78195cfa0c1e70a` |
| `apple-sdf-dev-v2/run.json` | completed | — | `e47b0b968efadd11d244189e27b258c40570719166d63664e08fda1739135033` |
| `apple-sdf-no-self-collision-v1/run.json` | completed | — | `62265759a0cfb5e060b972e7bcfbd214c0477f7377826a8b6b55865383e6aabf` |
| `apple-collision-filter-audit-v1/run.json` | completed | — | `a58e86df78d0fb7ac3b5f915f060c7956bf75e6789744811edd3bfc841dd79c6` |
| `apple-sdf-parent-filter-v1/run.json` | completed | — | `2e5ca9e946c133fa2fbf5717f67eaf876a03c85958da10eecc6f009fcb23ad06` |
| `contact-details-slide-v1/run.json` | error | — | `0491e133518ed0ef73f9a0f3ca48237887de91e24f0b0f07f61d9d5b1fce99cb` |
| `contact-details-slide-v2/run.json` | completed | — | `c3734680d3258686936b5f418702b41740687277847c573ee76f6952491424d3` |
| `apple-sdf-contact-details-v1/run.json` | completed | — | `e11e22b31598acdf32386b5d9fc2965bbb763128bf9c3547552dd868f1071eb3` |
| `apple-sdf-contact-details-500us-v1/run.json` | completed | — | `e7f66561cba0d58bf026969bc5eec7396b77cf3e20e2aaa5351aba3f25ad6dcc` |
| `apple-sdf-raised-approach-v1/run.json` | completed | — | `a3fa2e767cc112da64ef42fc1f60c1135cd6904191d3add94edf32be8db999f7` |
| `apple-sdf-mid-approach-v1/run.json` | completed | — | `55d28742bbed58dd4ceb6331e8483bce1143f16f7250e5955ffe78439ddd9426` |

## apple-grasp-v1/development.json

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `apple-sdf-lower-stem-v1/run.json` | completed | — | `405617e72e9fb3e39012e1ae9001c39f5aee71289f5d81f55967473e379b4cc0` |
| `apple-sdf-torsion-1mm-v1/run.json` | completed | — | `bd88299178e64719ed02fdf7d5ab53723245af599f528464d15904c6c4699387` |
| `apple-sdf-torsion-high-v1/run.json` | completed | — | `ae46ea8e627e5928bbac225371b167e62ca73f6dc413c615a9a818790f5f0f4c` |
| `apple-sdf-torsion-mid-v1/run.json` | completed | — | `f567295ab6aa610e23fab2ba6ab8c5b9dba2d19b9c5cabdbc3025ad380de5e74` |
| `apple-sdf-torsion-mid-high-v1/run.json` | completed | — | `9cb496a8870e7fe9360eacb3b1bad8db50b246b2141aad603db20b59702f6724` |
| `apple-public-closure095-v1/run.json` | completed | — | `9db54d5b0710345d021ee3237a8790a7edd9c4b20965ddf386f3cc6124ac9d85` |
| `apple-public-closure095-v2/run.json` | completed | H+K | `ad936efaf960eb900e938f0ad3866dc239a232818937fde4ed4a3c6359b04c76` |
| `apple-public-no-torsion-v1/run.json` | completed | H+K | `6b90c7d728b435e0266745d7275b61658f44f377dcfabd8722977f219a07cf49` |

## robot-parent-filter-v1

See the matching cohort and archive links in the audit. / 证据入口见审计报告同名批次。

| Receipt / 回执 | Status / 状态 | Packages / 包 | SHA256 |
|---|---|---|---|
| `robot-parent-filter-release-v1/run.json` | completed | H+K | `0ec677b445266bd2edda3ee41faa6c94500a33e89436973ed118b917fe46e697` |
