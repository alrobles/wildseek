import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

export const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Timeline (Total: 5400 frames = 180s = 3:00 min @ 30fps):
  // 1. Cold Open (Peer-Reviewed Science x AI Acceleration): 0 - 600 (0:00 - 0:20)
  // 2. Act 1 - The Panzootic Threat (74 mammals, 82M birds, egg prices): 600 - 1200 (0:20 - 0:40)
  // 3. Act 2 - Automated ML at Biological Scale (101,376 fits, M mask, ROC-AUC 0.74): 1200 - 2550 (0:40 - 1:25)
  // 4. Act 3 - Fine-Tuned Decision Models & litmine (LoRA 0.0->0.70, 3.4x recall): 2550 - 3900 (1:25 - 2:10)
  // 5. Act 4 - Self-Feeding Architecture & 4-Gate Quorum (03:15 cron, 2,247 HUC8, QA): 3900 - 4950 (2:10 - 2:45)
  // 6. End Card - Applied AI for Real-World Impact (wildseek.ecoseek.org): 4950 - 5400 (2:45 - 3:00)

  const getOpacity = (start: number, end: number, fade = 20) => {
    return interpolate(
      frame,
      [start, start + fade, end - fade, end],
      [0, 1, 1, 0],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );
  };

  const opColdOpen = getOpacity(0, 600);
  const opAct1 = getOpacity(600, 1200);
  const opAct2 = getOpacity(1200, 2550);
  const opAct3 = getOpacity(2550, 3900);
  const opAct4 = getOpacity(3900, 4950);
  const opEndCard = interpolate(frame, [4950, 4975], [0, 1], {
    extrapolateRight: 'clamp',
    extrapolateLeft: 'clamp',
  });

  const slowZoom = interpolate(frame % 1350, [0, 1350], [1, 1.05], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#070b14',
        color: '#f8fafc',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        overflow: 'hidden',
      }}
    >
      {/* Ambient Lights */}
      <div
        style={{
          position: 'absolute',
          top: '-15%',
          left: '15%',
          width: '70vw',
          height: '70vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, rgba(7, 11, 20, 0) 70%)',
          filter: 'blur(100px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '-15%',
          right: '10%',
          width: '60vw',
          height: '60vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(56, 189, 248, 0.06) 0%, rgba(7, 11, 20, 0) 70%)',
          filter: 'blur(90px)',
          pointerEvents: 'none',
        }}
      />

      {/* PERSISTENT HEADER BAR */}
      <div
        style={{
          position: 'absolute',
          top: 36,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 50,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#10b981',
              boxShadow: '0 0 14px #10b981',
            }}
          />
          <span style={{ fontSize: 28, fontWeight: 900, letterSpacing: '-0.5px' }}>
            WildSeek <span style={{ color: '#10b981' }}>·</span> Applied Science × Meta AI
          </span>
        </div>
        <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
          <div
            style={{
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              color: '#34d399',
              padding: '6px 18px',
              borderRadius: 999,
              fontSize: 15,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.8px',
            }}
          >
            Built During Event Window
          </div>
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              padding: '6px 18px',
              borderRadius: 999,
              fontSize: 15,
              fontWeight: 600,
              color: '#94a3b8',
            }}
          >
            Meta Global AI Hackathon
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 1. COLD OPEN: PEER-REVIEWED SCIENCE x AI ACCELERATION (0:00 - 0:20 / frames 0-600) */}
      {/* ========================================================= */}
      {frame < 600 && (
        <AbsoluteFill
          style={{
            opacity: opColdOpen,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '100px 120px 140px 120px',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 36 }}>
            <div
              style={{
                fontSize: 18,
                color: '#34d399',
                fontWeight: 800,
                letterSpacing: '3px',
                textTransform: 'uppercase',
                marginBottom: 10,
              }}
            >
              Not a Chatbot · Applied Biosurveillance Engineering
            </div>
            <h1 style={{ fontSize: 58, fontWeight: 900, margin: 0, letterSpacing: '-1.5px' }}>
              From Peer-Reviewed Algorithm to Enterprise Monitor in Days
            </h1>
          </div>

          <div style={{ display: 'flex', gap: 40, width: '100%', maxWidth: 1420 }}>
            {/* Scientific Foundations */}
            <div
              style={{
                flex: 1,
                background: 'rgba(30, 41, 59, 0.4)',
                border: '1px solid rgba(148, 163, 184, 0.2)',
                borderRadius: 20,
                padding: '36px 40px',
              }}
            >
              <div
                style={{
                  fontSize: 20,
                  fontWeight: 800,
                  color: '#94a3b8',
                  textTransform: 'uppercase',
                  marginBottom: 18,
                }}
              >
                Macroecological Foundations (Priors)
              </div>
              <ul
                style={{
                  listStyle: 'none',
                  padding: 0,
                  margin: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                  fontSize: 21,
                  color: '#cbd5e1',
                }}
              >
                <li>🧬 <b>PNAS 2022 3-Distance Framework</b> (Robles-Fernández et al.)</li>
                <li>⚡ <b>xnicher & oneearthr</b> (Bivariate ellipsoid niche engine)</li>
                <li>🌳 <b>BirdTree & Mammal Consensus Trees</b> (True patristic branch lengths)</li>
                <li>🌐 <b>GBIF / USDA APHIS / ERA5-Land</b> (Continuous environmental surfaces)</li>
              </ul>
            </div>

            {/* AI-Empowered Production System */}
            <div
              style={{
                flex: 1,
                background: 'rgba(16, 185, 129, 0.08)',
                border: '2px solid rgba(16, 185, 129, 0.5)',
                borderRadius: 20,
                padding: '36px 40px',
                boxShadow: '0 20px 40px -10px rgba(16, 185, 129, 0.15)',
              }}
            >
              <div
                style={{
                  fontSize: 20,
                  fontWeight: 800,
                  color: '#34d399',
                  textTransform: 'uppercase',
                  marginBottom: 18,
                }}
              >
                AI-Driven Build (Built This Week)
              </div>
              <ul
                style={{
                  listStyle: 'none',
                  padding: 0,
                  margin: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                  fontSize: 21,
                  color: '#ffffff',
                }}
              >
                <li>🎯 <b>101,376 automated climate fits</b> with accessible area (M) masks</li>
                <li>🤖 <b>LoRA-adapted Glimmer-30B</b> model (0.00 → 0.70 exact match)</li>
                <li>📚 <b>Autonomous litmine factory</b>: 4,854 edges @ $0.0014/edge (100% precision)</li>
                <li>🔄 <b>Self-feeding nightly pipeline</b> with strict 4-gate deployment quorum</li>
              </ul>
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* ========================================================= */}
      {/* 2. ACT 1: THE PANZOOTIC THREAT (0:20 - 0:40 / frames 600-1200) */}
      {/* ========================================================= */}
      {frame >= 600 && frame < 1200 && (
        <AbsoluteFill
          style={{
            opacity: opAct1,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '110px 100px 140px 100px',
          }}
        >
          <div style={{ display: 'flex', gap: 60, alignItems: 'center', width: '100%', maxWidth: 1520 }}>
            <div style={{ flex: 1.2 }}>
              <div
                style={{
                  fontSize: 18,
                  color: '#f87171',
                  fontWeight: 800,
                  letterSpacing: '2px',
                  textTransform: 'uppercase',
                  marginBottom: 12,
                }}
              >
                H5N1 Clade 2.3.4.4b Spillover Crisis
              </div>
              <h2
                style={{
                  fontSize: 56,
                  fontWeight: 900,
                  lineHeight: 1.1,
                  margin: '0 0 22px 0',
                  letterSpacing: '-1px',
                }}
              >
                Jumping Species & Threatening the Agrarian Food Supply
              </h2>
              <p style={{ fontSize: 25, color: '#94a3b8', lineHeight: 1.5, margin: '0 0 30px 0' }}>
                Traditional surveillance is lagging and reactive — logging carcass die-offs after transmission has already occurred. WildSeek delivers prospective intelligence, projecting spillover before cattle herds and poultry facilities are exposed.
              </p>
              <div style={{ display: 'flex', gap: 20 }}>
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '16px 24px',
                    borderRadius: 16,
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <div style={{ fontSize: 13, color: '#94a3b8' }}>Poultry Flocks</div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: '#f87171' }}>82M+ Birds</div>
                </div>
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '16px 24px',
                    borderRadius: 16,
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <div style={{ fontSize: 13, color: '#94a3b8' }}>Mammal Spillovers</div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: '#ef4444' }}>74 Species</div>
                </div>
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '16px 24px',
                    borderRadius: 16,
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <div style={{ fontSize: 13, color: '#94a3b8' }}>APHIS Positives</div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: '#f59e0b' }}>9,139 Points</div>
                </div>
              </div>
            </div>

            <div style={{ flex: 0.9, position: 'relative' }}>
              <div
                style={{
                  borderRadius: 20,
                  overflow: 'hidden',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  boxShadow: '0 25px 50px rgba(0,0,0,0.6)',
                }}
              >
                <Img src={staticFile('egg_prices.png')} style={{ width: '100%', height: 'auto', display: 'block' }} />
              </div>
              <div
                style={{
                  position: 'absolute',
                  bottom: -18,
                  right: 20,
                  background: 'rgba(15, 23, 42, 0.92)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  padding: '10px 20px',
                  borderRadius: 12,
                  fontSize: 14,
                  color: '#94a3b8',
                }}
              >
                Direct farmgate shocks & supply-chain exposure
              </div>
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* ========================================================= */}
      {/* 3. ACT 2: AUTOMATED ML AT BIOLOGICAL SCALE (0:40 - 1:25 / frames 1200-2550) */}
      {/* ========================================================= */}
      {frame >= 1200 && frame < 2550 && (
        <AbsoluteFill
          style={{
            opacity: opAct2,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '110px 80px 140px 80px',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div
              style={{
                fontSize: 18,
                color: '#38bdf8',
                fontWeight: 800,
                letterSpacing: '3px',
                textTransform: 'uppercase',
                marginBottom: 8,
              }}
            >
              Macroecological Machine Learning Factory
            </div>
            <h2 style={{ fontSize: 54, fontWeight: 900, margin: 0, letterSpacing: '-1px' }}>
              101,376 Niche Models · Accessible Area (M) · Prospective AUC 0.74
            </h2>
          </div>

          <div style={{ display: 'flex', gap: 40, width: '100%', maxWidth: 1560, height: '62%' }}>
            {/* Interactive Monitor Preview */}
            <div
              style={{
                flex: 1.3,
                borderRadius: 20,
                overflow: 'hidden',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                boxShadow: '0 25px 60px rgba(0,0,0,0.6)',
                position: 'relative',
              }}
            >
              <Img
                src={staticFile('site.png')}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  transform: `scale(${slowZoom})`,
                }}
              />
            </div>

            {/* Scientific Architecture Cards */}
            <div style={{ flex: 0.9, display: 'flex', flexDirection: 'column', gap: 18, justifyContent: 'center' }}>
              <div
                style={{
                  background: 'rgba(30, 41, 59, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '22px 26px',
                  borderRadius: 16,
                }}
              >
                <div style={{ fontSize: 15, color: '#34d399', fontWeight: 700, textTransform: 'uppercase', marginBottom: 4 }}>
                  1. Accessible Area (M) & ERA5-Land
                </div>
                <div style={{ fontSize: 19, color: '#f8fafc', lineHeight: 1.4 }}>
                  88 candidate ellipsoid pairs per species tested against 30-year climate normals. Bounded to occupied RESOLVE ecoregions to prevent pseudo-absence bias.
                </div>
              </div>

              <div
                style={{
                  background: 'rgba(30, 41, 59, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '22px 26px',
                  borderRadius: 16,
                }}
              >
                <div style={{ fontSize: 15, color: '#38bdf8', fontWeight: 700, textTransform: 'uppercase', marginBottom: 4 }}>
                  2. True Patristic Distances (AVONET Crosswalk)
                </div>
                <div style={{ fontSize: 19, color: '#f8fafc', lineHeight: 1.4 }}>
                  968/1,147 species mapped on real posterior consensus branch lengths (BirdTree Stage2 & dated mammal tree), resolving 202/208 historically proxied taxa.
                </div>
              </div>

              <div
                style={{
                  background: 'rgba(30, 41, 59, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '22px 26px',
                  borderRadius: 16,
                }}
              >
                <div style={{ fontSize: 15, color: '#f59e0b', fontWeight: 700, textTransform: 'uppercase', marginBottom: 4 }}>
                  3. Prospective Empirical Generalization
                </div>
                <div style={{ fontSize: 19, color: '#f8fafc', lineHeight: 1.4 }}>
                  Achieves <b>ROC-AUC 0.74 on 53 held-out hosts</b> evidenced in literature post-training (5-fold cross-validated AUC 0.862 ± 0.028).
                </div>
              </div>
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* ========================================================= */}
      {/* 4. ACT 3: FINE-TUNED DECISION MODELS & LITMINE (1:25 - 2:10 / frames 2550-3900) */}
      {/* ========================================================= */}
      {frame >= 2550 && frame < 3900 && (
        <AbsoluteFill
          style={{
            opacity: opAct3,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '110px 100px 140px 100px',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 34 }}>
            <div
              style={{
                fontSize: 18,
                color: '#a855f7',
                fontWeight: 800,
                letterSpacing: '3px',
                textTransform: 'uppercase',
                marginBottom: 8,
              }}
            >
              Meta Model Specialization & Autonomous Literature Factory
            </div>
            <h2 style={{ fontSize: 52, fontWeight: 900, margin: 0, letterSpacing: '-1px' }}>
              LoRA Decision Fine-Tuning & 3.4× Full-Text Extraction Advantage
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32, width: '100%', maxWidth: 1480 }}>
            {/* Box 1: Tail Audit */}
            <div
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(168, 85, 247, 0.4)',
                borderRadius: 20,
                padding: '32px 30px',
              }}
            >
              <div style={{ fontSize: 14, color: '#c084fc', fontWeight: 700, textTransform: 'uppercase', marginBottom: 12 }}>
                Meta muse-spark · Zero Hallucination
              </div>
              <div style={{ fontSize: 42, fontWeight: 900, color: '#ffffff', marginBottom: 10 }}>
                173 <span style={{ fontSize: 20, color: '#94a3b8', fontWeight: 500 }}>Tail Fits Audited</span>
              </div>
              <div style={{ fontSize: 18, color: '#cbd5e1', lineHeight: 1.5 }}>
                49 <b>flag_review</b> verdicts with machine-executable refit reasons serialized in <code>decisions_delta.csv</code>. Zero uninspected code mutation.
              </div>
            </div>

            {/* Box 2: LoRA SFT */}
            <div
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '2px solid rgba(56, 189, 248, 0.5)',
                borderRadius: 20,
                padding: '32px 30px',
                boxShadow: '0 15px 35px -5px rgba(56, 189, 248, 0.15)',
              }}
            >
              <div style={{ fontSize: 14, color: '#38bdf8', fontWeight: 700, textTransform: 'uppercase', marginBottom: 12 }}>
                Glimmer-30B LoRA Adapter
              </div>
              <div style={{ fontSize: 42, fontWeight: 900, color: '#38bdf8', marginBottom: 10 }}>
                0.00 → 0.70 <span style={{ fontSize: 20, color: '#94a3b8', fontWeight: 500 }}>Exact Match</span>
              </div>
              <div style={{ fontSize: 18, color: '#cbd5e1', lineHeight: 1.5 }}>
                Trained on Fireworks serverless ($0 promo). 28–0 paired win (p ≈ 7.5e-9). <b>0.82 semantic agreement</b> across complex all-task parsing.
              </div>
            </div>

            {/* Box 3: litmine Cascade */}
            <div
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                borderRadius: 20,
                padding: '32px 30px',
              }}
            >
              <div style={{ fontSize: 14, color: '#34d399', fontWeight: 700, textTransform: 'uppercase', marginBottom: 12 }}>
                PMC Full-Text Cascade (litmine)
              </div>
              <div style={{ fontSize: 42, fontWeight: 900, color: '#ffffff', marginBottom: 10 }}>
                4,854 <span style={{ fontSize: 20, color: '#94a3b8', fontWeight: 500 }}>Edges @ $0.0014</span>
              </div>
              <div style={{ fontSize: 18, color: '#cbd5e1', lineHeight: 1.5 }}>
                <b>56% vs 16% pair recall</b> over abstracts (3.4× boost). Capa-3 adversarial JUDGE reached <b>100% precision</b> on human verification audit.
              </div>
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* ========================================================= */}
      {/* 5. ACT 4: SELF-FEEDING ARCHITECTURE & 4-GATE QUORUM (2:10 - 2:45 / frames 3900-4950) */}
      {/* ========================================================= */}
      {frame >= 3900 && frame < 4950 && (
        <AbsoluteFill
          style={{
            opacity: opAct4,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '110px 100px 140px 100px',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 34 }}>
            <div
              style={{
                fontSize: 18,
                color: '#10b981',
                fontWeight: 800,
                letterSpacing: '3px',
                textTransform: 'uppercase',
                marginBottom: 8,
              }}
            >
              Living System · Continental Scale & Hard Governance
            </div>
            <h2 style={{ fontSize: 52, fontWeight: 900, margin: 0, letterSpacing: '-1px' }}>
              Nightly Autonomous Pipeline Across 2,247 Watersheds & 3,109 Counties
            </h2>
          </div>

          <div style={{ display: 'flex', gap: 40, width: '100%', maxWidth: 1500, alignItems: 'center' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div
                style={{
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '22px 28px',
                  borderRadius: 16,
                }}
              >
                <div style={{ fontSize: 28, fontWeight: 900, color: '#38bdf8', marginBottom: 4 }}>
                  2,247 HUC8 Watersheds & 3,109 Counties
                </div>
                <div style={{ fontSize: 17, color: '#94a3b8' }}>
                  Continuous risk computed as 90-day decayed detections × competent reservoir community, aggregated to hydrological sub-basins.
                </div>
              </div>

              <div
                style={{
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '2px solid rgba(16, 185, 129, 0.35)',
                  padding: '22px 28px',
                  borderRadius: 16,
                }}
              >
                <div style={{ fontSize: 28, fontWeight: 900, color: '#34d399', marginBottom: 4 }}>
                  03:15 Nightly Autonomous Cron
                </div>
                <div style={{ fontSize: 17, color: '#cbd5e1' }}>
                  Self-feeding pipeline pulls USDA APHIS REST endpoints, computes delta surfaces, and prepares production deployment bundles.
                </div>
              </div>

              <div
                style={{
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '22px 28px',
                  borderRadius: 16,
                }}
              >
                <div style={{ fontSize: 24, fontWeight: 800, color: '#f59e0b', marginBottom: 4 }}>
                  4-Member QA Approver Quorum (≥ 3/4)
                </div>
                <div style={{ fontSize: 16, color: '#cbd5e1' }}>
                  Evaluates <b>Code Gate</b> (schema checks), <b>Security Gate</b> (volume monotonicity), <b>UX Gate</b>, and <b>Brain Gate</b> (muse-spark audit) + hard cost veto.
                </div>
              </div>
            </div>

            <div
              style={{
                flex: 1,
                borderRadius: 20,
                overflow: 'hidden',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                boxShadow: '0 25px 60px rgba(0,0,0,0.6)',
              }}
            >
              <Img src={staticFile('site.png')} style={{ width: '100%', height: 'auto', display: 'block' }} />
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* ========================================================= */}
      {/* 6. END CARD: APPLIED AI FOR REAL-WORLD IMPACT (2:45 - 3:00 / frames 4950-5400) */}
      {/* ========================================================= */}
      {frame >= 4950 && (
        <AbsoluteFill
          style={{
            opacity: opEndCard,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            textAlign: 'center',
            padding: '0 100px',
          }}
        >
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.85)',
              border: '2px solid rgba(16, 185, 129, 0.4)',
              borderRadius: 28,
              padding: '64px 90px',
              maxWidth: 980,
              boxShadow: '0 30px 80px rgba(0,0,0,0.8)',
            }}
          >
            <div
              style={{
                fontSize: 18,
                color: '#34d399',
                fontWeight: 800,
                letterSpacing: '4px',
                textTransform: 'uppercase',
                marginBottom: 16,
              }}
            >
              Meta Global AI Developer Hackathon
            </div>
            <h1 style={{ fontSize: 70, fontWeight: 900, margin: '0 0 20px 0', letterSpacing: '-2px' }}>
              WildSeek Is Live
            </h1>
            <p style={{ fontSize: 26, color: '#94a3b8', margin: '0 0 40px 0', lineHeight: 1.5 }}>
              Applied science empowered by artificial intelligence to safeguard ecosystems and food supplies.
            </p>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <div
                style={{
                  background: '#10b981',
                  color: '#022c22',
                  fontWeight: 900,
                  fontSize: 28,
                  padding: '18px 48px',
                  borderRadius: 14,
                  letterSpacing: '0.5px',
                }}
              >
                wildseek.ecoseek.org
              </div>
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* ========================================================= */}
      {/* CAPTIONS SYNCHRONIZED BELOW (MATCHING THE WHITEPAPER SCRIPT) */}
      {/* ========================================================= */}
      <div
        style={{
          position: 'absolute',
          bottom: 70,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          pointerEvents: 'none',
          zIndex: 60,
        }}
      >
        <div
          style={{
            background: 'rgba(0, 0, 0, 0.86)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            padding: '12px 36px',
            borderRadius: 16,
            fontSize: 22,
            fontWeight: 600,
            color: '#f8fafc',
            maxWidth: '85%',
            textAlign: 'center',
            boxShadow: '0 10px 30px rgba(0,0,0,0.6)',
          }}
        >
          {frame < 600 &&
            'WildSeek is applied macroecology empowered by AI: pushing the PNAS 2022 framework into an enterprise monitor in days.'}
          {frame >= 600 && frame < 1200 &&
            'H5N1 has jumped to 74 mammal species and poultry affecting 82M+ birds. We predict where it spills over next.'}
          {frame >= 1200 && frame < 1875 &&
            '101,376 automated niche fits bounded by accessible area (M) masks against 30-year ERA5 climate normals.'}
          {frame >= 1875 && frame < 2550 &&
            'Phylogenetic distance on real consensus trees reconciled to GBIF taxonomy, achieving ROC-AUC 0.74 on 53 held-out hosts.'}
          {frame >= 2550 && frame < 3225 &&
            'Decision fine-tuning: Glimmer-30B LoRA jumped exact-match from 0.00 to 0.70 with 0.82 semantic agreement.'}
          {frame >= 3225 && frame < 3900 &&
            'Full-text literature cascade: 4,854 edges at $0.0014 each, achieving 3.4× recall over abstracts with 100% precision.'}
          {frame >= 3900 && frame < 4425 &&
            'Continental risk across 2,247 HUC8 watersheds and 3,109 counties exposed to dairy and commercial poultry.'}
          {frame >= 4425 && frame < 4950 &&
            'Self-feeding nightly 03:15 pipeline gated behind a 4-member QA quorum (Code, Security, UX, Brain) with cost veto.'}
          {frame >= 4950 &&
            'WildSeek is live now at wildseek.ecoseek.org.'}
        </div>
      </div>

      {/* PERSISTENT LEGAL FOOTER */}
      <div
        style={{
          position: 'absolute',
          bottom: 22,
          left: 0,
          right: 0,
          textAlign: 'center',
          fontSize: 14,
          fontWeight: 600,
          color: '#64748b',
          letterSpacing: '0.6px',
          zIndex: 60,
        }}
      >
        Ecological surveillance for wildlife professionals — not medical advice.
      </div>
    </AbsoluteFill>
  );
};
