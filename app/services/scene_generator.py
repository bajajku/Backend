"""Scene generator for LLM-generated 3D primitive scenes.

This module generates Three.js scenes using primitives (spheres, boxes, etc.)
based on a ConceptGraph, creating meaningful educational visualizations.
"""

import json
from typing import Any

import structlog

from app.models.analysis import ConceptGraph

logger = structlog.get_logger()


def generate_primitive_scene_html(
    graph: ConceptGraph,
    audio_data: dict[str, str],  # concept_id -> base64 audio data URI
) -> str:
    """Generate a complete HTML file with a 3D primitive scene.

    Args:
        graph: The concept graph defining the scene structure
        audio_data: Dictionary mapping concept IDs to base64 audio data URIs

    Returns:
        Complete HTML file as a string
    """
    logger.info(
        "generating_primitive_scene",
        title=graph.title,
        concepts=len(graph.concepts),
        relationships=len(graph.relationships),
        layout=graph.layout_type,
    )

    # Prepare concept data with audio
    concepts_with_audio = []
    for concept in graph.concepts:
        concept_dict = concept.model_dump()
        concept_dict["audio_url"] = audio_data.get(concept.id, "")
        concepts_with_audio.append(concept_dict)

    # Get category colors map
    category_colors = {cat.id: cat.color for cat in graph.categories}

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{graph.title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: {graph.background_color};
            color: white;
            overflow: hidden;
        }}

        #canvas-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}

        /* UI Layer */
        #ui {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 100;
        }}

        #title {{
            position: absolute;
            top: 30px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 1.8rem;
            font-weight: 300;
            letter-spacing: 3px;
            text-shadow: 0 0 20px rgba(100, 150, 255, 0.5);
            text-align: center;
            max-width: 80%;
        }}

        #summary {{
            position: absolute;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.95rem;
            opacity: 0.7;
            text-align: center;
            max-width: 600px;
            line-height: 1.5;
        }}

        /* Info Panel */
        #info-panel {{
            position: absolute;
            right: -420px;
            top: 50%;
            transform: translateY(-50%);
            width: 380px;
            padding: 30px;
            background: rgba(20, 20, 40, 0.85);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(100, 150, 255, 0.2);
            border-right: none;
            border-radius: 20px 0 0 20px;
            transition: right 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: auto;
            box-shadow: -10px 0 40px rgba(0, 0, 0, 0.5);
        }}

        #info-panel.visible {{
            right: 0;
        }}

        #info-panel h2 {{
            font-size: 1.4rem;
            font-weight: 400;
            margin-bottom: 15px;
            color: #6ea8fe;
        }}

        #info-panel .description {{
            font-size: 1rem;
            line-height: 1.7;
            opacity: 0.9;
            margin-bottom: 20px;
        }}

        #info-panel .category {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8rem;
            margin-bottom: 15px;
        }}

        #info-panel .related {{
            font-size: 0.85rem;
            opacity: 0.7;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}

        #close-btn {{
            position: absolute;
            top: 15px;
            right: 15px;
            width: 30px;
            height: 30px;
            border: none;
            background: rgba(255,255,255,0.1);
            color: white;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }}

        #close-btn:hover {{
            background: rgba(255,255,255,0.2);
        }}

        /* Tooltip */
        #tooltip {{
            position: fixed;
            padding: 8px 14px;
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid rgba(100, 150, 255, 0.4);
            border-radius: 6px;
            font-size: 0.85rem;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 200;
        }}

        #tooltip.visible {{
            opacity: 1;
        }}

        /* Help */
        #help {{
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.9rem;
            opacity: 0.5;
            transition: opacity 1s;
        }}

        /* Loading */
        #loader {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: {graph.background_color};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            transition: opacity 0.5s;
        }}

        #loader.hidden {{
            opacity: 0;
            pointer-events: none;
        }}

        .spinner {{
            width: 50px;
            height: 50px;
            border: 3px solid rgba(100, 150, 255, 0.2);
            border-top-color: #6ea8fe;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        /* Audio indicator */
        #audio-indicator {{
            position: absolute;
            bottom: 30px;
            right: 30px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 15px;
            background: rgba(0,0,0,0.5);
            border-radius: 20px;
            font-size: 0.85rem;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: auto;
        }}

        #audio-indicator.playing {{
            opacity: 1;
        }}

        .audio-bars {{
            display: flex;
            gap: 2px;
            height: 15px;
            align-items: flex-end;
        }}

        .audio-bar {{
            width: 3px;
            background: #6ea8fe;
            animation: audioBar 0.5s ease-in-out infinite alternate;
        }}

        .audio-bar:nth-child(1) {{ height: 40%; animation-delay: 0s; }}
        .audio-bar:nth-child(2) {{ height: 70%; animation-delay: 0.1s; }}
        .audio-bar:nth-child(3) {{ height: 50%; animation-delay: 0.2s; }}
        .audio-bar:nth-child(4) {{ height: 90%; animation-delay: 0.3s; }}
        .audio-bar:nth-child(5) {{ height: 60%; animation-delay: 0.4s; }}

        @keyframes audioBar {{
            to {{ height: 100%; }}
        }}

        /* Tour mode */
        #tour-btn {{
            position: absolute;
            bottom: 30px;
            left: 30px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #6ea8fe, #4a7cc9);
            border: none;
            border-radius: 25px;
            color: white;
            font-size: 0.9rem;
            cursor: pointer;
            pointer-events: auto;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px rgba(74, 124, 201, 0.3);
        }}

        #tour-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(74, 124, 201, 0.4);
        }}

        /* Mobile adjustments */
        @media (max-width: 768px) {{
            #title {{ font-size: 1.3rem; }}
            #summary {{ font-size: 0.85rem; top: 70px; }}
            #info-panel {{
                width: 100%;
                right: 0;
                bottom: -100%;
                top: auto;
                transform: none;
                border-radius: 20px 20px 0 0;
                max-height: 60vh;
                overflow-y: auto;
            }}
            #info-panel.visible {{
                bottom: 0;
            }}
        }}
    </style>
</head>
<body>
    <div id="canvas-container"></div>

    <div id="loader">
        <div class="spinner"></div>
        <div>Loading Experience...</div>
    </div>

    <div id="ui">
        <h1 id="title">{graph.title}</h1>
        <p id="summary">{graph.summary}</p>

        <div id="info-panel">
            <button id="close-btn">&times;</button>
            <span id="panel-category" class="category"></span>
            <h2 id="panel-title"></h2>
            <p id="panel-description" class="description"></p>
            <div id="panel-related" class="related"></div>
        </div>

        <div id="tooltip"></div>

        <div id="help">Click on concepts to explore • Drag to rotate • Scroll to zoom</div>

        <button id="tour-btn">▶ Start Guided Tour</button>

        <div id="audio-indicator">
            <div class="audio-bars">
                <div class="audio-bar"></div>
                <div class="audio-bar"></div>
                <div class="audio-bar"></div>
                <div class="audio-bar"></div>
                <div class="audio-bar"></div>
            </div>
            <span>Playing narration...</span>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <script type="importmap">
    {{
        "imports": {{
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
        }}
    }}
    </script>

    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ EffectComposer }} from 'three/addons/postprocessing/EffectComposer.js';
        import {{ RenderPass }} from 'three/addons/postprocessing/RenderPass.js';
        import {{ UnrealBloomPass }} from 'three/addons/postprocessing/UnrealBloomPass.js';

        // ============================================================
        // DATA
        // ============================================================
        const graphData = {{
            layoutType: {json.dumps(graph.layout_type)},
            centralConceptId: {json.dumps(graph.central_concept_id)},
            concepts: {json.dumps(concepts_with_audio)},
            relationships: {json.dumps([r.model_dump() for r in graph.relationships])},
            categories: {json.dumps({cat.id: {"name": cat.name, "color": cat.color} for cat in graph.categories})},
            explorationOrder: {json.dumps(graph.suggested_exploration_order)}
        }};

        // ============================================================
        // SCENE SETUP
        // ============================================================
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color('{graph.background_color}');

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 5, 15);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        // Post-processing
        const composer = new EffectComposer(renderer);
        composer.addPass(new RenderPass(scene, camera));
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            0.4, 0.4, 0.85
        );
        composer.addPass(bloomPass);

        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxDistance = 30;
        controls.minDistance = 5;

        // Lighting
        const ambientLight = new THREE.AmbientLight('{graph.ambient_color}', 0.4);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 20, 10);
        scene.add(directionalLight);

        // ============================================================
        // CREATE STARS
        // ============================================================
        const starGeo = new THREE.BufferGeometry();
        const starCount = 500;
        const starPositions = new Float32Array(starCount * 3);
        for (let i = 0; i < starCount * 3; i++) {{
            starPositions[i] = (Math.random() - 0.5) * 100;
        }}
        starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
        const starMat = new THREE.PointsMaterial({{ size: 0.1, color: 0x6ea8fe, transparent: true, opacity: 0.6 }});
        const stars = new THREE.Points(starGeo, starMat);
        scene.add(stars);

        // ============================================================
        // CREATE CONCEPT NODES
        // ============================================================
        const conceptMeshes = new Map();
        const conceptData = new Map();
        const conceptGroup = new THREE.Group();
        scene.add(conceptGroup);

        // Layout calculations
        function calculatePositions() {{
            const positions = new Map();
            const concepts = graphData.concepts;
            const centralId = graphData.centralConceptId;
            const layout = graphData.layoutType;

            if (layout === 'concept-map' || layout === 'network') {{
                // Central concept at origin, others in orbit
                const centralConcept = concepts.find(c => c.id === centralId);
                if (centralConcept) positions.set(centralId, new THREE.Vector3(0, 0, 0));

                const others = concepts.filter(c => c.id !== centralId);
                const radius = 6;
                others.forEach((c, i) => {{
                    const angle = (i / others.length) * Math.PI * 2;
                    const y = (c.importance - 3) * 0.5; // Vary height by importance
                    positions.set(c.id, new THREE.Vector3(
                        Math.cos(angle) * radius,
                        y,
                        Math.sin(angle) * radius
                    ));
                }});
            }} else if (layout === 'hierarchy') {{
                // Tree structure
                const levels = new Map();
                concepts.forEach(c => {{
                    const level = c.parent_id ? 1 : 0;
                    if (!levels.has(level)) levels.set(level, []);
                    levels.get(level).push(c);
                }});

                let y = 3;
                levels.forEach((levelConcepts, level) => {{
                    const width = levelConcepts.length * 4;
                    levelConcepts.forEach((c, i) => {{
                        const x = (i - (levelConcepts.length - 1) / 2) * 4;
                        positions.set(c.id, new THREE.Vector3(x, y, 0));
                    }});
                    y -= 4;
                }});
            }} else if (layout === 'timeline') {{
                // Linear progression
                concepts.forEach((c, i) => {{
                    positions.set(c.id, new THREE.Vector3(i * 4 - (concepts.length - 1) * 2, 0, 0));
                }});
            }} else if (layout === 'clusters') {{
                // Group by category
                const categories = new Map();
                concepts.forEach(c => {{
                    if (!categories.has(c.category)) categories.set(c.category, []);
                    categories.get(c.category).push(c);
                }});

                let catIndex = 0;
                const catCount = categories.size;
                categories.forEach((catConcepts, catId) => {{
                    const catAngle = (catIndex / catCount) * Math.PI * 2;
                    const catRadius = 8;
                    const catCenter = new THREE.Vector3(
                        Math.cos(catAngle) * catRadius,
                        0,
                        Math.sin(catAngle) * catRadius
                    );

                    catConcepts.forEach((c, i) => {{
                        const localAngle = (i / catConcepts.length) * Math.PI * 2;
                        const localRadius = 2;
                        positions.set(c.id, new THREE.Vector3(
                            catCenter.x + Math.cos(localAngle) * localRadius,
                            (c.importance - 3) * 0.3,
                            catCenter.z + Math.sin(localAngle) * localRadius
                        ));
                    }});
                    catIndex++;
                }});
            }}

            return positions;
        }}

        const positions = calculatePositions();

        // Create meshes for each concept
        graphData.concepts.forEach(concept => {{
            const category = graphData.categories[concept.category] || {{ color: '#6ea8fe' }};
            const color = concept.color || category.color;
            const size = 0.3 + (concept.importance / 5) * 0.5;

            let geometry;
            switch (concept.shape) {{
                case 'box':
                    geometry = new THREE.BoxGeometry(size, size, size);
                    break;
                case 'cylinder':
                    geometry = new THREE.CylinderGeometry(size * 0.5, size * 0.5, size, 16);
                    break;
                case 'cone':
                    geometry = new THREE.ConeGeometry(size * 0.5, size, 16);
                    break;
                case 'torus':
                    geometry = new THREE.TorusGeometry(size * 0.5, size * 0.2, 16, 32);
                    break;
                case 'octahedron':
                    geometry = new THREE.OctahedronGeometry(size * 0.6);
                    break;
                default:
                    geometry = new THREE.SphereGeometry(size * 0.6, 32, 32);
            }}

            const material = new THREE.MeshStandardMaterial({{
                color: color,
                emissive: color,
                emissiveIntensity: 0.2,
                roughness: 0.4,
                metalness: 0.3
            }});

            const mesh = new THREE.Mesh(geometry, material);
            const pos = positions.get(concept.id) || new THREE.Vector3(0, 0, 0);
            mesh.position.copy(pos);
            mesh.userData = {{ ...concept, baseY: pos.y, category: category }};

            conceptMeshes.set(concept.id, mesh);
            conceptData.set(concept.id, concept);
            conceptGroup.add(mesh);

            // Add label
            // Using sprite for simple labels
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = 256;
            canvas.height = 64;
            ctx.fillStyle = 'rgba(0,0,0,0.5)';
            ctx.fillRect(0, 0, 256, 64);
            ctx.fillStyle = 'white';
            ctx.font = 'bold 24px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(concept.name, 128, 40);

            const texture = new THREE.CanvasTexture(canvas);
            const spriteMaterial = new THREE.SpriteMaterial({{ map: texture, transparent: true }});
            const sprite = new THREE.Sprite(spriteMaterial);
            sprite.position.set(pos.x, pos.y + size + 0.5, pos.z);
            sprite.scale.set(2, 0.5, 1);
            conceptGroup.add(sprite);
            mesh.userData.label = sprite;
        }});

        // ============================================================
        // CREATE CONNECTIONS
        // ============================================================
        const connectionGroup = new THREE.Group();
        scene.add(connectionGroup);

        graphData.relationships.forEach(rel => {{
            const fromMesh = conceptMeshes.get(rel.from_id);
            const toMesh = conceptMeshes.get(rel.to_id);
            if (!fromMesh || !toMesh) return;

            const points = [fromMesh.position.clone(), toMesh.position.clone()];
            const geometry = new THREE.BufferGeometry().setFromPoints(points);

            const opacity = 0.2 + (rel.strength / 5) * 0.3;
            const material = new THREE.LineBasicMaterial({{
                color: 0x6ea8fe,
                transparent: true,
                opacity: opacity
            }});

            const line = new THREE.Line(geometry, material);
            line.userData = rel;
            connectionGroup.add(line);
        }});

        // ============================================================
        // INTERACTION
        // ============================================================
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        let hoveredMesh = null;
        let selectedMesh = null;
        let currentAudio = null;

        const tooltip = document.getElementById('tooltip');
        const infoPanel = document.getElementById('info-panel');
        const audioIndicator = document.getElementById('audio-indicator');

        function updateTooltip(e) {{
            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        }}

        function checkHover() {{
            raycaster.setFromCamera(mouse, camera);
            const meshes = Array.from(conceptMeshes.values());
            const intersects = raycaster.intersectObjects(meshes);

            if (intersects.length > 0) {{
                const mesh = intersects[0].object;
                if (hoveredMesh !== mesh) {{
                    if (hoveredMesh && hoveredMesh !== selectedMesh) {{
                        gsap.to(hoveredMesh.scale, {{ x: 1, y: 1, z: 1, duration: 0.3 }});
                    }}
                    hoveredMesh = mesh;
                    if (hoveredMesh !== selectedMesh) {{
                        gsap.to(hoveredMesh.scale, {{ x: 1.2, y: 1.2, z: 1.2, duration: 0.3, ease: 'back.out' }});
                    }}
                    tooltip.textContent = mesh.userData.name;
                    tooltip.classList.add('visible');
                    document.body.style.cursor = 'pointer';
                }}
            }} else {{
                if (hoveredMesh && hoveredMesh !== selectedMesh) {{
                    gsap.to(hoveredMesh.scale, {{ x: 1, y: 1, z: 1, duration: 0.3 }});
                }}
                hoveredMesh = null;
                tooltip.classList.remove('visible');
                document.body.style.cursor = 'default';
            }}
        }}

        function selectConcept(mesh) {{
            if (selectedMesh) {{
                gsap.to(selectedMesh.scale, {{ x: 1, y: 1, z: 1, duration: 0.3 }});
                selectedMesh.material.emissiveIntensity = 0.2;
            }}

            selectedMesh = mesh;
            const data = mesh.userData;

            // Update panel
            document.getElementById('panel-title').textContent = data.name;
            document.getElementById('panel-description').textContent = data.description;
            document.getElementById('panel-category').textContent = data.category.name || data.category;
            document.getElementById('panel-category').style.background = data.category.color || '#6ea8fe';

            // Find related concepts
            const related = graphData.relationships
                .filter(r => r.from_id === data.id || r.to_id === data.id)
                .map(r => {{
                    const otherId = r.from_id === data.id ? r.to_id : r.from_id;
                    const other = graphData.concepts.find(c => c.id === otherId);
                    return other ? other.name : null;
                }})
                .filter(Boolean);

            document.getElementById('panel-related').textContent =
                related.length ? 'Related: ' + related.join(', ') : '';

            infoPanel.classList.add('visible');

            // Animate
            gsap.to(mesh.scale, {{ x: 1.3, y: 1.3, z: 1.3, duration: 0.3 }});
            mesh.material.emissiveIntensity = 0.5;

            // Camera
            const targetPos = mesh.position.clone().add(new THREE.Vector3(0, 2, 5));
            gsap.to(camera.position, {{
                x: targetPos.x, y: targetPos.y, z: targetPos.z,
                duration: 1.2, ease: 'power2.inOut'
            }});
            gsap.to(controls.target, {{
                x: mesh.position.x, y: mesh.position.y, z: mesh.position.z,
                duration: 1.2
            }});

            // Dim others
            conceptMeshes.forEach((m, id) => {{
                if (m !== mesh) {{
                    gsap.to(m.material, {{ opacity: 0.3, transparent: true, duration: 0.5 }});
                }}
            }});

            // Highlight connections
            connectionGroup.children.forEach(line => {{
                const rel = line.userData;
                if (rel.from_id === data.id || rel.to_id === data.id) {{
                    gsap.to(line.material, {{ opacity: 0.8, duration: 0.5 }});
                }} else {{
                    gsap.to(line.material, {{ opacity: 0.05, duration: 0.5 }});
                }}
            }});

            // Play audio
            if (data.audio_url) {{
                if (currentAudio) {{
                    currentAudio.pause();
                    currentAudio = null;
                }}
                currentAudio = new Audio(data.audio_url);
                currentAudio.play().then(() => {{
                    audioIndicator.classList.add('playing');
                }}).catch(e => console.log('Audio play failed:', e));
                currentAudio.onended = () => {{
                    audioIndicator.classList.remove('playing');
                }};
            }}
        }}

        function deselectConcept() {{
            if (!selectedMesh) return;

            gsap.to(selectedMesh.scale, {{ x: 1, y: 1, z: 1, duration: 0.3 }});
            selectedMesh.material.emissiveIntensity = 0.2;
            selectedMesh = null;

            infoPanel.classList.remove('visible');

            // Restore all
            conceptMeshes.forEach(m => {{
                gsap.to(m.material, {{ opacity: 1, duration: 0.5 }});
            }});
            connectionGroup.children.forEach(line => {{
                const opacity = 0.2 + (line.userData.strength / 5) * 0.3;
                gsap.to(line.material, {{ opacity: opacity, duration: 0.5 }});
            }});

            // Camera back
            gsap.to(camera.position, {{ x: 0, y: 5, z: 15, duration: 1.2, ease: 'power2.inOut' }});
            gsap.to(controls.target, {{ x: 0, y: 0, z: 0, duration: 1.2 }});

            if (currentAudio) {{
                currentAudio.pause();
                currentAudio = null;
                audioIndicator.classList.remove('playing');
            }}
        }}

        // Event listeners
        window.addEventListener('mousemove', updateTooltip);
        window.addEventListener('click', () => {{
            if (hoveredMesh) {{
                selectConcept(hoveredMesh);
            }} else if (selectedMesh) {{
                deselectConcept();
            }}
        }});

        document.getElementById('close-btn').addEventListener('click', (e) => {{
            e.stopPropagation();
            deselectConcept();
        }});

        // ============================================================
        // GUIDED TOUR
        // ============================================================
        let tourActive = false;
        let tourIndex = 0;

        document.getElementById('tour-btn').addEventListener('click', () => {{
            if (tourActive) {{
                tourActive = false;
                document.getElementById('tour-btn').textContent = '▶ Start Guided Tour';
                deselectConcept();
            }} else {{
                tourActive = true;
                tourIndex = 0;
                document.getElementById('tour-btn').textContent = '⏹ Stop Tour';
                nextTourStep();
            }}
        }});

        function nextTourStep() {{
            if (!tourActive) return;

            const order = graphData.explorationOrder.length > 0
                ? graphData.explorationOrder
                : graphData.concepts.map(c => c.id);

            if (tourIndex >= order.length) {{
                tourActive = false;
                document.getElementById('tour-btn').textContent = '▶ Start Guided Tour';
                deselectConcept();
                return;
            }}

            const conceptId = order[tourIndex];
            const mesh = conceptMeshes.get(conceptId);
            if (mesh) {{
                selectConcept(mesh);

                // Wait for audio to finish, then move to next
                if (currentAudio) {{
                    currentAudio.onended = () => {{
                        audioIndicator.classList.remove('playing');
                        tourIndex++;
                        setTimeout(nextTourStep, 1000);
                    }};
                }} else {{
                    tourIndex++;
                    setTimeout(nextTourStep, 3000);
                }}
            }} else {{
                tourIndex++;
                nextTourStep();
            }}
        }}

        // ============================================================
        // ANIMATION LOOP
        // ============================================================
        const clock = new THREE.Clock();

        function animate() {{
            requestAnimationFrame(animate);
            const time = clock.getElapsedTime();

            // Floating animation
            conceptMeshes.forEach((mesh, id) => {{
                if (mesh !== selectedMesh) {{
                    mesh.position.y = mesh.userData.baseY + Math.sin(time + mesh.position.x) * 0.1;
                    mesh.rotation.y += 0.003;
                }}
            }});

            // Star twinkle
            starMat.opacity = 0.4 + Math.sin(time * 0.5) * 0.2;
            stars.rotation.y += 0.0002;

            checkHover();
            controls.update();
            composer.render();
        }}

        // ============================================================
        // RESIZE
        // ============================================================
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
            composer.setSize(window.innerWidth, window.innerHeight);
        }});

        // ============================================================
        // INIT
        // ============================================================
        setTimeout(() => {{
            document.getElementById('loader').classList.add('hidden');
            setTimeout(() => {{
                document.getElementById('help').style.opacity = '0';
            }}, 5000);
        }}, 500);

        animate();
    </script>
</body>
</html>'''

    logger.info("primitive_scene_generated", size_bytes=len(html.encode("utf-8")))
    return html
