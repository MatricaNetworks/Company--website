/**
 * Matrica Networks - WebGL Shaders
 * Vertex and fragment shaders for the 3D globe/shield visualization
 */

// Vertex shader for the rotating globe/shield
const vertexShaderSource = `
    attribute vec3 aPosition;
    attribute vec3 aNormal;
    attribute vec2 aTexCoord;
    
    uniform mat4 uModelMatrix;
    uniform mat4 uViewMatrix;
    uniform mat4 uProjectionMatrix;
    uniform mat4 uNormalMatrix;
    uniform float uTime;
    
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying vec2 vTexCoord;
    varying vec3 vWorldPosition;
    varying float vPulse;
    
    void main() {
        // Calculate pulse effect based on time
        vPulse = sin(uTime * 2.0) * 0.5 + 0.5;
        
        // Transform position with slight pulsing effect
        vec3 position = aPosition * (1.0 + vPulse * 0.1);
        
        // Calculate world position
        vWorldPosition = (uModelMatrix * vec4(position, 1.0)).xyz;
        
        // Transform normal
        vNormal = normalize((uNormalMatrix * vec4(aNormal, 0.0)).xyz);
        
        // Pass through texture coordinates
        vTexCoord = aTexCoord;
        vPosition = position;
        
        // Final vertex position
        gl_Position = uProjectionMatrix * uViewMatrix * uModelMatrix * vec4(position, 1.0);
    }
`;

// Fragment shader for neon glow effect
const fragmentShaderSource = `
    precision mediump float;
    
    uniform float uTime;
    uniform vec3 uCameraPosition;
    uniform vec3 uNeonColor;
    uniform float uGlowIntensity;
    uniform bool uWireframe;
    
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying vec2 vTexCoord;
    varying vec3 vWorldPosition;
    varying float vPulse;
    
    // Noise function for procedural effects
    float random(vec2 st) {
        return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
    }
    
    float noise(vec2 st) {
        vec2 i = floor(st);
        vec2 f = fract(st);
        
        float a = random(i);
        float b = random(i + vec2(1.0, 0.0));
        float c = random(i + vec2(0.0, 1.0));
        float d = random(i + vec2(1.0, 1.0));
        
        vec2 u = f * f * (3.0 - 2.0 * f);
        
        return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
    }
    
    void main() {
        vec3 normal = normalize(vNormal);
        vec3 viewDirection = normalize(uCameraPosition - vWorldPosition);
        
        // Fresnel effect for edge glow
        float fresnel = pow(1.0 - dot(normal, viewDirection), 2.0);
        
        // Base color with neon tint
        vec3 baseColor = uNeonColor;
        
        // Grid pattern for cyberpunk effect
        vec2 grid = fract(vTexCoord * 10.0);
        float gridLine = step(0.9, max(grid.x, grid.y)) * 0.5;
        
        // Circuit pattern using noise
        float circuit = noise(vTexCoord * 8.0 + uTime * 0.5);
        circuit = step(0.6, circuit) * 0.3;
        
        // Pulse effect based on position and time
        float pulse = sin(length(vPosition) * 5.0 - uTime * 3.0) * 0.5 + 0.5;
        
        if (uWireframe) {
            // Wireframe mode - emphasize edges and grid
            float wireframeGlow = fresnel * uGlowIntensity;
            vec3 color = baseColor * (wireframeGlow + gridLine + circuit);
            color *= (1.0 + vPulse * 0.5);
            
            // Add scanning line effect
            float scanLine = sin(vWorldPosition.y * 10.0 + uTime * 5.0);
            scanLine = smoothstep(0.8, 1.0, scanLine) * 0.3;
            color += vec3(0.0, 1.0, 1.0) * scanLine;
            
            gl_FragColor = vec4(color, 0.7 + fresnel * 0.3);
        } else {
            // Solid mode - holographic effect
            vec3 color = baseColor;
            
            // Holographic interference pattern
            float hologram = sin(vWorldPosition.x * 20.0) * sin(vWorldPosition.y * 20.0) * 0.1;
            color += hologram * vec3(1.0, 0.5, 1.0);
            
            // Fresnel rim lighting
            color *= (0.3 + fresnel * 0.7);
            
            // Add circuit details
            color += circuit * vec3(0.0, 1.0, 0.5);
            
            // Pulse effect
            color *= (0.8 + pulse * 0.4);
            
            gl_FragColor = vec4(color, 0.6 + fresnel * 0.4);
        }
    }
`;

// Particle system vertex shader for ambient effects
const particleVertexShaderSource = `
    attribute vec3 aPosition;
    attribute float aSize;
    attribute float aLife;
    
    uniform mat4 uModelMatrix;
    uniform mat4 uViewMatrix;
    uniform mat4 uProjectionMatrix;
    uniform float uTime;
    
    varying float vLife;
    varying float vSize;
    
    void main() {
        vLife = aLife;
        vSize = aSize;
        
        // Orbital motion
        float orbit = uTime * 0.5 + aPosition.x * 0.1;
        vec3 position = aPosition;
        position.x = cos(orbit) * length(aPosition.xz);
        position.z = sin(orbit) * length(aPosition.xz);
        
        gl_Position = uProjectionMatrix * uViewMatrix * uModelMatrix * vec4(position, 1.0);
        gl_PointSize = aSize * (1.0 + sin(uTime + aPosition.x) * 0.5);
    }
`;

// Particle system fragment shader
const particleFragmentShaderSource = `
    precision mediump float;
    
    uniform vec3 uParticleColor;
    uniform float uTime;
    
    varying float vLife;
    varying float vSize;
    
    void main() {
        // Circular particle shape
        vec2 center = gl_PointCoord - vec2(0.5);
        float distance = length(center);
        
        if (distance > 0.5) {
            discard;
        }
        
        // Glow effect
        float glow = 1.0 - (distance * 2.0);
        glow = pow(glow, 2.0);
        
        // Fade based on life
        float alpha = vLife * glow * 0.6;
        
        // Flickering effect
        float flicker = sin(uTime * 10.0 + vSize * 100.0) * 0.5 + 0.5;
        alpha *= (0.7 + flicker * 0.3);
        
        gl_FragColor = vec4(uParticleColor * glow, alpha);
    }
`;

// Shield geometry vertex shader
const shieldVertexShaderSource = `
    attribute vec3 aPosition;
    attribute vec3 aNormal;
    
    uniform mat4 uModelMatrix;
    uniform mat4 uViewMatrix;
    uniform mat4 uProjectionMatrix;
    uniform mat4 uNormalMatrix;
    uniform float uTime;
    uniform float uShieldStrength;
    
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying vec3 vWorldPosition;
    varying float vShieldEffect;
    
    void main() {
        // Shield deformation based on strength
        vec3 position = aPosition;
        float deform = sin(uTime * 3.0 + length(aPosition) * 5.0) * 0.05 * uShieldStrength;
        position += aNormal * deform;
        
        vPosition = position;
        vWorldPosition = (uModelMatrix * vec4(position, 1.0)).xyz;
        vNormal = normalize((uNormalMatrix * vec4(aNormal, 0.0)).xyz);
        vShieldEffect = uShieldStrength;
        
        gl_Position = uProjectionMatrix * uViewMatrix * uModelMatrix * vec4(position, 1.0);
    }
`;

// Shield fragment shader with energy field effect
const shieldFragmentShaderSource = `
    precision mediump float;
    
    uniform float uTime;
    uniform vec3 uCameraPosition;
    uniform vec3 uShieldColor;
    uniform float uShieldStrength;
    uniform vec3 uImpactPoint;
    uniform float uImpactIntensity;
    
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying vec3 vWorldPosition;
    varying float vShieldEffect;
    
    // Hexagonal pattern function
    float hexPattern(vec2 uv, float scale) {
        uv *= scale;
        vec2 grid = abs(fract(uv) - 0.5);
        return max(grid.x, grid.y);
    }
    
    void main() {
        vec3 normal = normalize(vNormal);
        vec3 viewDirection = normalize(uCameraPosition - vWorldPosition);
        
        // Fresnel effect
        float fresnel = pow(1.0 - dot(normal, viewDirection), 1.5);
        
        // Hexagonal energy pattern
        vec2 sphericalUV = vec2(
            atan(vPosition.z, vPosition.x) / (2.0 * 3.14159) + 0.5,
            asin(vPosition.y / length(vPosition)) / 3.14159 + 0.5
        );
        
        float hexGrid = hexPattern(sphericalUV, 8.0);
        hexGrid = 1.0 - smoothstep(0.4, 0.5, hexGrid);
        
        // Energy flow animation
        float flow = sin(uTime * 2.0 + sphericalUV.x * 10.0) * 0.5 + 0.5;
        flow *= sin(uTime * 1.5 + sphericalUV.y * 8.0) * 0.5 + 0.5;
        
        // Impact effect
        float impactDistance = length(vWorldPosition - uImpactPoint);
        float impact = smoothstep(2.0, 0.0, impactDistance) * uImpactIntensity;
        
        // Combine effects
        vec3 color = uShieldColor;
        color *= fresnel * 0.7 + 0.3;
        color *= hexGrid * 0.8 + 0.2;
        color *= flow * 0.6 + 0.4;
        color += impact * vec3(1.0, 0.5, 0.0);
        
        // Shield strength affects visibility
        float alpha = fresnel * vShieldEffect * 0.6;
        alpha += hexGrid * vShieldEffect * 0.3;
        alpha += impact * 0.5;
        
        gl_FragColor = vec4(color, alpha);
    }
`;

// Utility function to create shader program
function createShaderProgram(gl, vertexSource, fragmentSource) {
    function compileShader(gl, source, type) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            const error = gl.getShaderInfoLog(shader);
            gl.deleteShader(shader);
            throw new Error(`Shader compilation error: ${error}`);
        }
        
        return shader;
    }
    
    const vertexShader = compileShader(gl, vertexSource, gl.VERTEX_SHADER);
    const fragmentShader = compileShader(gl, fragmentSource, gl.FRAGMENT_SHADER);
    
    const program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        const error = gl.getProgramInfoLog(program);
        gl.deleteProgram(program);
        throw new Error(`Program linking error: ${error}`);
    }
    
    // Clean up shaders
    gl.deleteShader(vertexShader);
    gl.deleteShader(fragmentShader);
    
    return program;
}

// Export shader sources and utility
window.WebGLShaders = {
    vertexShaderSource,
    fragmentShaderSource,
    particleVertexShaderSource,
    particleFragmentShaderSource,
    shieldVertexShaderSource,
    shieldFragmentShaderSource,
    createShaderProgram
};