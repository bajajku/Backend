"""Anatomical 3D model generator using LLM-generated Three.js code.

This module generates actual 3D anatomical/subject-specific models
rather than abstract concept nodes. The LLM creates the Three.js geometry
code directly for maximum creativity and accuracy.
"""

import json
import re

import structlog

from app.utils.llm import LLM

logger = structlog.get_logger()


def _clean_json_response(text: str) -> str:
    """Clean LLM JSON response by removing common issues.
    
    Args:
        text: Raw JSON text from LLM
        
    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    # Remove single-line comments (// ...)
    text = re.sub(r'//[^\n]*\n', '\n', text)
    
    # Remove trailing commas before } or ]
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Remove any leading/trailing whitespace
    text = text.strip()
    
    return text


def _parse_json_safely(text: str) -> dict:
    """Parse JSON with fallback strategies.
    
    Args:
        text: JSON text to parse
        
    Returns:
        Parsed dictionary
        
    Raises:
        json.JSONDecodeError: If all parsing attempts fail
    """
    # First try: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Second try: clean and parse
    cleaned = _clean_json_response(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Third try: find JSON object in text
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # All attempts failed, raise with original error
    return json.loads(text)


ANATOMICAL_SCENE_PROMPT = """You are an expert 3D modeler and Three.js developer.
Your task: Create a 3D model that visually represents the subject matter from this document.

Instead of abstract shapes, create an ACTUAL 3D representation of the content:
- For brain anatomy → create a 3D brain with lobes, brainstem, cerebellum
- For solar system → create planets orbiting a sun
- For human heart → create chambers, valves, arteries
- For molecules → create atoms and bonds
- For history/timeline → create a 3D timeline with event markers
- For biology/cells → create cell structures with organelles

Return a JSON object with this EXACT structure:

{{
  "title": "3D Model Title",
  "summary": "2-3 sentence summary of what this model shows",
  "background_color": "#0a0a1a",
  
  "legend": [
    {{"color": "#ff9999", "label": "Part Name", "description": "What this represents"}}
  ],
  
  "parts": [
    {{
      "id": "unique_id",
      "name": "Display Name",
      "description": "Detailed explanation (2-3 sentences). This will be read aloud when clicked.",
      "geometry_code": "Three.js geometry creation code",
      "material_code": "Three.js material creation code", 
      "position": [x, y, z],
      "rotation": [rx, ry, rz],
      "scale": [sx, sy, sz]
    }}
  ],
  
  "camera_position": [x, y, z],
  "animation_code": "Optional: JavaScript code for animating the scene"
}}

GEOMETRY CODE EXAMPLES:

1. Sphere (for rounded structures like brain lobes):
   "new THREE.SphereGeometry(1, 32, 32)"

2. Scaled sphere (elongated):
   "(() => {{ const g = new THREE.SphereGeometry(1, 32, 32); g.scale(1, 0.8, 1.2); return g; }})()"

3. Cylinder (for tubes like brainstem, arteries):
   "new THREE.CylinderGeometry(0.2, 0.1, 1.5, 32)"

4. Torus (for rings, orbits):
   "new THREE.TorusGeometry(5, 0.1, 16, 100)"

5. Box (for rectangular structures):
   "new THREE.BoxGeometry(1, 2, 0.5)"

MATERIAL CODE EXAMPLES:

1. Standard colored material:
   "new THREE.MeshPhongMaterial({{ color: 0xff9999, shininess: 50 }})"

2. Transparent material:
   "new THREE.MeshPhongMaterial({{ color: 0x99ccff, transparent: true, opacity: 0.7 }})"

3. Emissive (glowing) material:
   "new THREE.MeshStandardMaterial({{ color: 0xffff00, emissive: 0xffff00, emissiveIntensity: 0.5 }})"

IMPORTANT GUIDELINES:

1. Create an ACCURATE visual representation of the subject
2. Use appropriate colors that are meaningful (e.g., arteries=red, veins=blue)
3. Position parts correctly relative to each other
4. Each part should have a clear, educational description for audio narration
5. Include a legend explaining what each color represents
6. Keep geometry simple but recognizable
7. Use 5-15 parts for a good balance of detail and clarity

DOCUMENT CONTENT:
{content}

Return ONLY valid JSON. No markdown, no explanation."""


class AnatomicalModelError(Exception):
    """Raised when anatomical model generation fails."""
    pass


async def generate_anatomical_model(content: str, llm: LLM) -> dict:
    """Generate anatomical 3D model specification from document content.
    
    Args:
        content: The extracted text content from the document
        llm: LLM instance for generation
        
    Returns:
        Dictionary with model specification
        
    Raises:
        AnatomicalModelError: If generation fails
    """
    logger.info("generating_anatomical_model", content_length=len(content))
    
    # Truncate content if too long
    truncated_content = content[:15000]
    if len(content) > 15000:
        logger.info("content_truncated", original=len(content), truncated=15000)
    
    prompt = ANATOMICAL_SCENE_PROMPT.format(content=truncated_content)
    
    try:
        response = await llm.generate_json(prompt)
        model_spec = _parse_json_safely(response)
        
        logger.info(
            "anatomical_model_generated",
            title=model_spec.get("title", "Unknown"),
            parts=len(model_spec.get("parts", [])),
        )
        
        return model_spec
        
    except json.JSONDecodeError as e:
        logger.error(
            "anatomical_model_json_parse_failed", 
            error=str(e),
            response_preview=response[:500] if response else "empty"
        )
        raise AnatomicalModelError(f"Failed to parse model JSON: {str(e)}") from e
    except Exception as e:
        logger.error("anatomical_model_generation_failed", error=str(e))
        raise AnatomicalModelError(f"Model generation failed: {str(e)}") from e


def generate_anatomical_scene_html(
    model_spec: dict,
    audio_data: dict[str, str],  # part_id -> base64 audio data URI
) -> str:
    """Generate complete HTML with anatomical 3D model.
    
    Args:
        model_spec: The model specification from LLM
        audio_data: Dictionary mapping part IDs to base64 audio data URIs
        
    Returns:
        Complete HTML file as a string
    """
    title = model_spec.get("title", "3D Model")
    summary = model_spec.get("summary", "")
    background_color = model_spec.get("background_color", "#0a0a1a")
    camera_pos = model_spec.get("camera_position", [0, 2, 5])
    parts = model_spec.get("parts", [])
    legend = model_spec.get("legend", [])
    animation_code = model_spec.get("animation_code", "")
    
    # Add audio URLs to parts
    parts_with_audio = []
    for part in parts:
        part_copy = part.copy()
        part_copy["audio_url"] = audio_data.get(part["id"], "")
        parts_with_audio.append(part_copy)
    
    # Generate legend HTML
    legend_html = "\n".join([
        f'<div class="legend-item"><span class="color-box" style="background:{item["color"]}"></span>{item["label"]}</div>'
        for item in legend
    ])
    
    # Generate parts creation JavaScript
    parts_js = _generate_parts_js(parts_with_audio)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: {background_color};
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
        
        /* Info Panel */
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            color: #333;
            padding: 20px;
            border-radius: 12px;
            max-width: 320px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 100;
        }}
        
        #info h1 {{
            font-size: 1.4rem;
            margin-bottom: 10px;
            color: #1a1a2e;
        }}
        
        #info p {{
            font-size: 0.9rem;
            line-height: 1.5;
            opacity: 0.8;
        }}
        
        /* Legend */
        #legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            color: #333;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 100;
            max-width: 280px;
        }}
        
        #legend h3 {{
            font-size: 0.9rem;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.7;
        }}
        
        .legend-item {{
            margin: 8px 0;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
        }}
        
        .color-box {{
            display: inline-block;
            width: 16px;
            height: 16px;
            margin-right: 10px;
            border-radius: 4px;
            flex-shrink: 0;
        }}
        
        /* Detail Panel (appears on click) */
        #detail-panel {{
            position: absolute;
            top: 50%;
            right: -400px;
            transform: translateY(-50%);
            width: 360px;
            background: rgba(255, 255, 255, 0.98);
            color: #333;
            padding: 25px;
            border-radius: 15px 0 0 15px;
            box-shadow: -5px 0 30px rgba(0,0,0,0.3);
            transition: right 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 200;
        }}
        
        #detail-panel.visible {{
            right: 0;
        }}
        
        #detail-panel h2 {{
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #1a1a2e;
        }}
        
        #detail-panel .description {{
            font-size: 0.95rem;
            line-height: 1.7;
            margin-bottom: 20px;
        }}
        
        #close-btn {{
            position: absolute;
            top: 15px;
            right: 15px;
            width: 32px;
            height: 32px;
            border: none;
            background: #f0f0f0;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        #close-btn:hover {{
            background: #e0e0e0;
        }}
        
        /* Audio Indicator */
        #audio-indicator {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 18px;
            background: rgba(0,0,0,0.8);
            border-radius: 25px;
            font-size: 0.85rem;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 100;
        }}
        
        #audio-indicator.playing {{
            opacity: 1;
        }}
        
        .audio-bars {{
            display: flex;
            gap: 3px;
            height: 18px;
            align-items: flex-end;
        }}
        
        .audio-bar {{
            width: 3px;
            background: #4ecdc4;
            animation: audioBar 0.5s ease-in-out infinite alternate;
        }}
        
        .audio-bar:nth-child(1) {{ height: 40%; animation-delay: 0s; }}
        .audio-bar:nth-child(2) {{ height: 70%; animation-delay: 0.1s; }}
        .audio-bar:nth-child(3) {{ height: 50%; animation-delay: 0.2s; }}
        .audio-bar:nth-child(4) {{ height: 90%; animation-delay: 0.3s; }}
        
        @keyframes audioBar {{
            to {{ height: 100%; }}
        }}
        
        /* Instructions */
        #instructions {{
            position: absolute;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.85rem;
            opacity: 0.6;
            text-align: center;
            z-index: 50;
        }}
        
        /* Loading */
        #loader {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: {background_color};
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
            border: 3px solid rgba(255,255,255,0.2);
            border-top-color: #4ecdc4;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="canvas-container"></div>
    
    <div id="loader">
        <div class="spinner"></div>
        <div>Loading 3D Model...</div>
    </div>
    
    <div id="info">
        <h1>{title}</h1>
        <p>{summary}</p>
    </div>
    
    <div id="legend">
        <h3>Legend</h3>
        {legend_html}
    </div>
    
    <div id="detail-panel">
        <button id="close-btn">&times;</button>
        <h2 id="detail-title"></h2>
        <p id="detail-description" class="description"></p>
    </div>
    
    <div id="audio-indicator">
        <div class="audio-bars">
            <div class="audio-bar"></div>
            <div class="audio-bar"></div>
            <div class="audio-bar"></div>
            <div class="audio-bar"></div>
        </div>
        <span>Playing narration...</span>
    </div>
    
    <div id="instructions">Click on any part to learn more • Drag to rotate • Scroll to zoom</div>

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

        // Scene Setup
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color('{background_color}');
        
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set({camera_pos[0]}, {camera_pos[1]}, {camera_pos[2]});
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);
        
        // Post-processing
        const composer = new EffectComposer(renderer);
        composer.addPass(new RenderPass(scene, camera));
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            0.3, 0.4, 0.85
        );
        composer.addPass(bloomPass);
        
        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(5, 10, 7);
        scene.add(directionalLight);
        
        const backLight = new THREE.DirectionalLight(0xffffff, 0.3);
        backLight.position.set(-5, -5, -5);
        scene.add(backLight);
        
        // Store parts for interaction
        const partsData = {json.dumps(parts_with_audio)};
        const partMeshes = new Map();
        
        // Create model parts
        {parts_js}
        
        // Interaction
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        let hoveredMesh = null;
        let selectedMesh = null;
        let currentAudio = null;
        
        const detailPanel = document.getElementById('detail-panel');
        const audioIndicator = document.getElementById('audio-indicator');
        
        function onMouseMove(event) {{
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
        }}
        
        function checkHover() {{
            raycaster.setFromCamera(mouse, camera);
            const meshes = Array.from(partMeshes.values());
            const intersects = raycaster.intersectObjects(meshes);
            
            if (intersects.length > 0) {{
                const mesh = intersects[0].object;
                if (hoveredMesh !== mesh) {{
                    if (hoveredMesh && hoveredMesh !== selectedMesh) {{
                        gsap.to(hoveredMesh.scale, {{ x: 1, y: 1, z: 1, duration: 0.3 }});
                    }}
                    hoveredMesh = mesh;
                    if (hoveredMesh !== selectedMesh) {{
                        gsap.to(hoveredMesh.scale, {{ x: 1.1, y: 1.1, z: 1.1, duration: 0.3 }});
                    }}
                    document.body.style.cursor = 'pointer';
                }}
            }} else {{
                if (hoveredMesh && hoveredMesh !== selectedMesh) {{
                    gsap.to(hoveredMesh.scale, {{ x: 1, y: 1, z: 1, duration: 0.3 }});
                }}
                hoveredMesh = null;
                document.body.style.cursor = 'default';
            }}
        }}
        
        function selectPart(mesh) {{
            if (selectedMesh) {{
                gsap.to(selectedMesh.scale, {{ x: 1, y: 1, z: 1, duration: 0.3 }});
                selectedMesh.material.emissiveIntensity = 0;
            }}
            
            selectedMesh = mesh;
            const data = mesh.userData;
            
            // Update detail panel
            document.getElementById('detail-title').textContent = data.name;
            document.getElementById('detail-description').textContent = data.description;
            detailPanel.classList.add('visible');
            
            // Highlight selected
            gsap.to(mesh.scale, {{ x: 1.15, y: 1.15, z: 1.15, duration: 0.3 }});
            if (mesh.material.emissive) {{
                mesh.material.emissiveIntensity = 0.3;
            }}
            
            // Dim others
            partMeshes.forEach((m) => {{
                if (m !== mesh) {{
                    gsap.to(m.material, {{ opacity: 0.3, transparent: true, duration: 0.4 }});
                }}
            }});
            
            // Play audio
            if (data.audio_url) {{
                if (currentAudio) {{
                    currentAudio.pause();
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
        
        function deselectPart() {{
            if (!selectedMesh) return;
            
            gsap.to(selectedMesh.scale, {{ x: 1, y: 1, z: 1, duration: 0.3 }});
            if (selectedMesh.material.emissive) {{
                selectedMesh.material.emissiveIntensity = 0;
            }}
            selectedMesh = null;
            
            detailPanel.classList.remove('visible');
            
            // Restore all
            partMeshes.forEach((m) => {{
                gsap.to(m.material, {{ opacity: 1, duration: 0.4 }});
            }});
            
            if (currentAudio) {{
                currentAudio.pause();
                currentAudio = null;
                audioIndicator.classList.remove('playing');
            }}
        }}
        
        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('click', () => {{
            if (hoveredMesh) {{
                selectPart(hoveredMesh);
            }} else if (selectedMesh) {{
                deselectPart();
            }}
        }});
        
        document.getElementById('close-btn').addEventListener('click', (e) => {{
            e.stopPropagation();
            deselectPart();
        }});
        
        // Animation loop
        const clock = new THREE.Clock();
        
        function animate() {{
            requestAnimationFrame(animate);
            const time = clock.getElapsedTime();
            
            // Custom animation from LLM (if provided)
            {f"try {{ {animation_code} }} catch(e) {{}}" if animation_code else ""}
            
            checkHover();
            controls.update();
            composer.render();
        }}
        
        // Resize handler
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
            composer.setSize(window.innerWidth, window.innerHeight);
        }});
        
        // Hide loader
        setTimeout(() => {{
            document.getElementById('loader').classList.add('hidden');
            setTimeout(() => {{
                document.getElementById('instructions').style.opacity = '0';
            }}, 5000);
        }}, 500);
        
        animate();
    </script>
</body>
</html>'''
    
    logger.info("anatomical_scene_generated", size_bytes=len(html.encode("utf-8")))
    return html


def _generate_parts_js(parts: list[dict]) -> str:
    """Generate JavaScript code to create all model parts."""
    js_lines = []
    
    for part in parts:
        part_id = part.get("id", "unknown")
        name = part.get("name", "Unknown Part")
        description = part.get("description", "")
        geometry_code = part.get("geometry_code", "new THREE.SphereGeometry(0.5, 32, 32)")
        material_code = part.get("material_code", "new THREE.MeshPhongMaterial({ color: 0xcccccc })")
        position = part.get("position", [0, 0, 0])
        rotation = part.get("rotation", [0, 0, 0])
        scale = part.get("scale", [1, 1, 1])
        audio_url = part.get("audio_url", "")
        
        js = f'''
        try {{
            const geo_{part_id} = {geometry_code};
            const mat_{part_id} = {material_code};
            const mesh_{part_id} = new THREE.Mesh(geo_{part_id}, mat_{part_id});
            mesh_{part_id}.position.set({position[0]}, {position[1]}, {position[2]});
            mesh_{part_id}.rotation.set({rotation[0]}, {rotation[1]}, {rotation[2]});
            mesh_{part_id}.scale.set({scale[0]}, {scale[1]}, {scale[2]});
            mesh_{part_id}.userData = {{
                id: {json.dumps(part_id)},
                name: {json.dumps(name)},
                description: {json.dumps(description)},
                audio_url: {json.dumps(audio_url)}
            }};
            scene.add(mesh_{part_id});
            partMeshes.set({json.dumps(part_id)}, mesh_{part_id});
        }} catch(e) {{
            console.warn('Failed to create part {part_id}:', e);
        }}'''
        js_lines.append(js)
    
    return "\n".join(js_lines)
