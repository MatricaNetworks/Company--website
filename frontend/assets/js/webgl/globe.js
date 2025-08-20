/**
 * Matrica Networks - WebGL 3D Globe/Shield
 * Raw WebGL implementation of rotating cybersecurity visualization
 */

class MatricaGlobe {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error(`Canvas with id ${canvasId} not found`);
        }
        
        this.gl = null;
        this.programs = {};
        this.buffers = {};
        this.textures = {};
        this.uniforms = {};
        
        // Configuration
        this.config = {
            wireframe: true,
            shield: false,
            particles: true,
            autoRotate: true,
            rotationSpeed: 0.5,
            glowIntensity: 1.0,
            neonColor: [0.0, 1.0, 1.0], // Cyan
            shieldColor: [0.0, 0.5, 1.0], // Blue
            particleColor: [0.0, 1.0, 0.5], // Green
            ...options
        };
        
        // Animation state
        this.time = 0;
        this.rotation = { x: 0, y: 0, z: 0 };
        this.camera = {
            position: [0, 0, 5],
            target: [0, 0, 0],
            up: [0, 1, 0]
        };
        
        // Interaction state
        this.mouse = { x: 0, y: 0, down: false };
        this.lastMouse = { x: 0, y: 0 };
        
        // Initialize WebGL
        this.init();
    }
    
    init() {
        try {
            // Get WebGL context
            this.gl = this.canvas.getContext('webgl') || this.canvas.getContext('experimental-webgl');
            if (!this.gl) {
                throw new Error('WebGL not supported');
            }
            
            // Set canvas size
            this.resize();
            
            // Initialize WebGL settings
            this.setupWebGL();
            
            // Create shader programs
            this.createPrograms();
            
            // Create geometry
            this.createGeometry();
            
            // Setup event listeners
            this.setupEvents();
            
            // Start animation loop
            this.animate();
            
            console.log('Matrica WebGL Globe initialized successfully');
            
        } catch (error) {
            console.error('WebGL initialization failed:', error);
            this.showFallback();
        }
    }
    
    setupWebGL() {
        const gl = this.gl;
        
        // Enable depth testing
        gl.enable(gl.DEPTH_TEST);
        gl.depthFunc(gl.LEQUAL);
        
        // Enable blending for transparency
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        
        // Set clear color to transparent black
        gl.clearColor(0.0, 0.0, 0.0, 0.0);
        
        // Enable face culling
        gl.enable(gl.CULL_FACE);
        gl.cullFace(gl.BACK);
    }
    
    createPrograms() {
        const gl = this.gl;
        
        // Main globe/shield program
        this.programs.globe = WebGLShaders.createShaderProgram(
            gl,
            WebGLShaders.vertexShaderSource,
            WebGLShaders.fragmentShaderSource
        );
        
        // Particle system program
        this.programs.particles = WebGLShaders.createShaderProgram(
            gl,
            WebGLShaders.particleVertexShaderSource,
            WebGLShaders.particleFragmentShaderSource
        );
        
        // Shield program
        this.programs.shield = WebGLShaders.createShaderProgram(
            gl,
            WebGLShaders.shieldVertexShaderSource,
            WebGLShaders.shieldFragmentShaderSource
        );
        
        // Get uniform locations
        this.getUniformLocations();
    }
    
    getUniformLocations() {
        const gl = this.gl;
        
        // Globe uniforms
        this.uniforms.globe = {
            uModelMatrix: gl.getUniformLocation(this.programs.globe, 'uModelMatrix'),
            uViewMatrix: gl.getUniformLocation(this.programs.globe, 'uViewMatrix'),
            uProjectionMatrix: gl.getUniformLocation(this.programs.globe, 'uProjectionMatrix'),
            uNormalMatrix: gl.getUniformLocation(this.programs.globe, 'uNormalMatrix'),
            uTime: gl.getUniformLocation(this.programs.globe, 'uTime'),
            uCameraPosition: gl.getUniformLocation(this.programs.globe, 'uCameraPosition'),
            uNeonColor: gl.getUniformLocation(this.programs.globe, 'uNeonColor'),
            uGlowIntensity: gl.getUniformLocation(this.programs.globe, 'uGlowIntensity'),
            uWireframe: gl.getUniformLocation(this.programs.globe, 'uWireframe')
        };
        
        // Particle uniforms
        this.uniforms.particles = {
            uModelMatrix: gl.getUniformLocation(this.programs.particles, 'uModelMatrix'),
            uViewMatrix: gl.getUniformLocation(this.programs.particles, 'uViewMatrix'),
            uProjectionMatrix: gl.getUniformLocation(this.programs.particles, 'uProjectionMatrix'),
            uTime: gl.getUniformLocation(this.programs.particles, 'uTime'),
            uParticleColor: gl.getUniformLocation(this.programs.particles, 'uParticleColor')
        };
        
        // Shield uniforms
        this.uniforms.shield = {
            uModelMatrix: gl.getUniformLocation(this.programs.shield, 'uModelMatrix'),
            uViewMatrix: gl.getUniformLocation(this.programs.shield, 'uViewMatrix'),
            uProjectionMatrix: gl.getUniformLocation(this.programs.shield, 'uProjectionMatrix'),
            uNormalMatrix: gl.getUniformLocation(this.programs.shield, 'uNormalMatrix'),
            uTime: gl.getUniformLocation(this.programs.shield, 'uTime'),
            uCameraPosition: gl.getUniformLocation(this.programs.shield, 'uCameraPosition'),
            uShieldColor: gl.getUniformLocation(this.programs.shield, 'uShieldColor'),
            uShieldStrength: gl.getUniformLocation(this.programs.shield, 'uShieldStrength'),
            uImpactPoint: gl.getUniformLocation(this.programs.shield, 'uImpactPoint'),
            uImpactIntensity: gl.getUniformLocation(this.programs.shield, 'uImpactIntensity')
        };
    }
    
    createGeometry() {
        this.createSphere();
        this.createParticles();
    }
    
    createSphere() {
        const gl = this.gl;
        const radius = 1.0;
        const segments = 32;
        const rings = 16;
        
        const positions = [];
        const normals = [];
        const texCoords = [];
        const indices = [];
        
        // Generate vertices
        for (let ring = 0; ring <= rings; ring++) {
            const theta = (ring * Math.PI) / rings;
            const sinTheta = Math.sin(theta);
            const cosTheta = Math.cos(theta);
            
            for (let segment = 0; segment <= segments; segment++) {
                const phi = (segment * 2 * Math.PI) / segments;
                const sinPhi = Math.sin(phi);
                const cosPhi = Math.cos(phi);
                
                const x = cosPhi * sinTheta;
                const y = cosTheta;
                const z = sinPhi * sinTheta;
                
                positions.push(x * radius, y * radius, z * radius);
                normals.push(x, y, z);
                texCoords.push(segment / segments, ring / rings);
            }
        }
        
        // Generate indices
        for (let ring = 0; ring < rings; ring++) {
            for (let segment = 0; segment < segments; segment++) {
                const first = ring * (segments + 1) + segment;
                const second = first + segments + 1;
                
                indices.push(first, second, first + 1);
                indices.push(second, second + 1, first + 1);
            }
        }
        
        // Create buffers
        this.buffers.sphere = {
            position: this.createBuffer(new Float32Array(positions)),
            normal: this.createBuffer(new Float32Array(normals)),
            texCoord: this.createBuffer(new Float32Array(texCoords)),
            indices: this.createIndexBuffer(new Uint16Array(indices)),
            indexCount: indices.length
        };
    }
    
    createParticles() {
        const gl = this.gl;
        const particleCount = 200;
        
        const positions = [];
        const sizes = [];
        const lives = [];
        
        for (let i = 0; i < particleCount; i++) {
            // Random position in sphere around globe
            const radius = 1.5 + Math.random() * 2.0;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;
            
            const x = Math.cos(theta) * Math.sin(phi) * radius;
            const y = Math.cos(phi) * radius;
            const z = Math.sin(theta) * Math.sin(phi) * radius;
            
            positions.push(x, y, z);
            sizes.push(2.0 + Math.random() * 4.0);
            lives.push(Math.random());
        }
        
        this.buffers.particles = {
            position: this.createBuffer(new Float32Array(positions)),
            size: this.createBuffer(new Float32Array(sizes)),
            life: this.createBuffer(new Float32Array(lives)),
            count: particleCount
        };
    }
    
    createBuffer(data) {
        const gl = this.gl;
        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
        return buffer;
    }
    
    createIndexBuffer(data) {
        const gl = this.gl;
        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, data, gl.STATIC_DRAW);
        return buffer;
    }
    
    setupEvents() {
        // Mouse interaction
        this.canvas.addEventListener('mousedown', (e) => {
            this.mouse.down = true;
            this.lastMouse.x = e.clientX;
            this.lastMouse.y = e.clientY;
        });
        
        this.canvas.addEventListener('mouseup', () => {
            this.mouse.down = false;
        });
        
        this.canvas.addEventListener('mousemove', (e) => {
            if (this.mouse.down) {
                const deltaX = e.clientX - this.lastMouse.x;
                const deltaY = e.clientY - this.lastMouse.y;
                
                this.rotation.y += deltaX * 0.01;
                this.rotation.x += deltaY * 0.01;
                
                this.lastMouse.x = e.clientX;
                this.lastMouse.y = e.clientY;
            }
        });
        
        // Touch support
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            this.mouse.down = true;
            this.lastMouse.x = touch.clientX;
            this.lastMouse.y = touch.clientY;
        });
        
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.mouse.down = false;
        });
        
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (this.mouse.down && e.touches.length > 0) {
                const touch = e.touches[0];
                const deltaX = touch.clientX - this.lastMouse.x;
                const deltaY = touch.clientY - this.lastMouse.y;
                
                this.rotation.y += deltaX * 0.01;
                this.rotation.x += deltaY * 0.01;
                
                this.lastMouse.x = touch.clientX;
                this.lastMouse.y = touch.clientY;
            }
        });
        
        // Resize handler
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        const rect = this.canvas.getBoundingClientRect();
        const displayWidth = rect.width;
        const displayHeight = rect.height;
        
        if (this.canvas.width !== displayWidth || this.canvas.height !== displayHeight) {
            this.canvas.width = displayWidth;
            this.canvas.height = displayHeight;
            
            if (this.gl) {
                this.gl.viewport(0, 0, displayWidth, displayHeight);
            }
        }
    }
    
    animate() {
        this.time += 0.016; // Assume 60fps
        
        if (this.config.autoRotate && !this.mouse.down) {
            this.rotation.y += 0.005 * this.config.rotationSpeed;
        }
        
        this.render();
        requestAnimationFrame(() => this.animate());
    }
    
    render() {
        const gl = this.gl;
        
        // Clear canvas
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        
        // Create matrices
        const modelMatrix = this.createModelMatrix();
        const viewMatrix = this.createViewMatrix();
        const projectionMatrix = this.createProjectionMatrix();
        const normalMatrix = this.createNormalMatrix(modelMatrix);
        
        // Render particles first (background)
        if (this.config.particles) {
            this.renderParticles(modelMatrix, viewMatrix, projectionMatrix);
        }
        
        // Render main globe/shield
        this.renderGlobe(modelMatrix, viewMatrix, projectionMatrix, normalMatrix);
        
        // Render shield overlay if enabled
        if (this.config.shield) {
            this.renderShield(modelMatrix, viewMatrix, projectionMatrix, normalMatrix);
        }
    }
    
    renderGlobe(modelMatrix, viewMatrix, projectionMatrix, normalMatrix) {
        const gl = this.gl;
        
        gl.useProgram(this.programs.globe);
        
        // Set uniforms
        gl.uniformMatrix4fv(this.uniforms.globe.uModelMatrix, false, modelMatrix);
        gl.uniformMatrix4fv(this.uniforms.globe.uViewMatrix, false, viewMatrix);
        gl.uniformMatrix4fv(this.uniforms.globe.uProjectionMatrix, false, projectionMatrix);
        gl.uniformMatrix4fv(this.uniforms.globe.uNormalMatrix, false, normalMatrix);
        gl.uniform1f(this.uniforms.globe.uTime, this.time);
        gl.uniform3fv(this.uniforms.globe.uCameraPosition, this.camera.position);
        gl.uniform3fv(this.uniforms.globe.uNeonColor, this.config.neonColor);
        gl.uniform1f(this.uniforms.globe.uGlowIntensity, this.config.glowIntensity);
        gl.uniform1i(this.uniforms.globe.uWireframe, this.config.wireframe);
        
        // Bind buffers and draw
        this.bindSphereBuffers(this.programs.globe);
        
        if (this.config.wireframe) {
            gl.drawElements(gl.LINES, this.buffers.sphere.indexCount, gl.UNSIGNED_SHORT, 0);
        } else {
            gl.drawElements(gl.TRIANGLES, this.buffers.sphere.indexCount, gl.UNSIGNED_SHORT, 0);
        }
    }
    
    renderParticles(modelMatrix, viewMatrix, projectionMatrix) {
        const gl = this.gl;
        
        gl.useProgram(this.programs.particles);
        
        // Set uniforms
        gl.uniformMatrix4fv(this.uniforms.particles.uModelMatrix, false, modelMatrix);
        gl.uniformMatrix4fv(this.uniforms.particles.uViewMatrix, false, viewMatrix);
        gl.uniformMatrix4fv(this.uniforms.particles.uProjectionMatrix, false, projectionMatrix);
        gl.uniform1f(this.uniforms.particles.uTime, this.time);
        gl.uniform3fv(this.uniforms.particles.uParticleColor, this.config.particleColor);
        
        // Bind particle buffers
        this.bindParticleBuffers(this.programs.particles);
        
        gl.drawArrays(gl.POINTS, 0, this.buffers.particles.count);
    }
    
    renderShield(modelMatrix, viewMatrix, projectionMatrix, normalMatrix) {
        const gl = this.gl;
        
        gl.useProgram(this.programs.shield);
        
        // Scale up slightly for shield
        const shieldMatrix = mat4.scale(mat4.create(), modelMatrix, [1.1, 1.1, 1.1]);
        
        // Set uniforms
        gl.uniformMatrix4fv(this.uniforms.shield.uModelMatrix, false, shieldMatrix);
        gl.uniformMatrix4fv(this.uniforms.shield.uViewMatrix, false, viewMatrix);
        gl.uniformMatrix4fv(this.uniforms.shield.uProjectionMatrix, false, projectionMatrix);
        gl.uniformMatrix4fv(this.uniforms.shield.uNormalMatrix, false, normalMatrix);
        gl.uniform1f(this.uniforms.shield.uTime, this.time);
        gl.uniform3fv(this.uniforms.shield.uCameraPosition, this.camera.position);
        gl.uniform3fv(this.uniforms.shield.uShieldColor, this.config.shieldColor);
        gl.uniform1f(this.uniforms.shield.uShieldStrength, 0.8);
        gl.uniform3fv(this.uniforms.shield.uImpactPoint, [0, 0, 0]);
        gl.uniform1f(this.uniforms.shield.uImpactIntensity, 0.0);
        
        // Bind buffers and draw
        this.bindSphereBuffers(this.programs.shield);
        gl.drawElements(gl.TRIANGLES, this.buffers.sphere.indexCount, gl.UNSIGNED_SHORT, 0);
    }
    
    bindSphereBuffers(program) {
        const gl = this.gl;
        
        // Position attribute
        const aPosition = gl.getAttribLocation(program, 'aPosition');
        gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.sphere.position);
        gl.vertexAttribPointer(aPosition, 3, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(aPosition);
        
        // Normal attribute
        const aNormal = gl.getAttribLocation(program, 'aNormal');
        if (aNormal >= 0) {
            gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.sphere.normal);
            gl.vertexAttribPointer(aNormal, 3, gl.FLOAT, false, 0, 0);
            gl.enableVertexAttribArray(aNormal);
        }
        
        // Texture coordinate attribute
        const aTexCoord = gl.getAttribLocation(program, 'aTexCoord');
        if (aTexCoord >= 0) {
            gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.sphere.texCoord);
            gl.vertexAttribPointer(aTexCoord, 2, gl.FLOAT, false, 0, 0);
            gl.enableVertexAttribArray(aTexCoord);
        }
        
        // Bind indices
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.buffers.sphere.indices);
    }
    
    bindParticleBuffers(program) {
        const gl = this.gl;
        
        // Position attribute
        const aPosition = gl.getAttribLocation(program, 'aPosition');
        gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.particles.position);
        gl.vertexAttribPointer(aPosition, 3, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(aPosition);
        
        // Size attribute
        const aSize = gl.getAttribLocation(program, 'aSize');
        if (aSize >= 0) {
            gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.particles.size);
            gl.vertexAttribPointer(aSize, 1, gl.FLOAT, false, 0, 0);
            gl.enableVertexAttribArray(aSize);
        }
        
        // Life attribute
        const aLife = gl.getAttribLocation(program, 'aLife');
        if (aLife >= 0) {
            gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.particles.life);
            gl.vertexAttribPointer(aLife, 1, gl.FLOAT, false, 0, 0);
            gl.enableVertexAttribArray(aLife);
        }
    }
    
    createModelMatrix() {
        const matrix = mat4.create();
        mat4.rotateX(matrix, matrix, this.rotation.x);
        mat4.rotateY(matrix, matrix, this.rotation.y);
        mat4.rotateZ(matrix, matrix, this.rotation.z);
        return matrix;
    }
    
    createViewMatrix() {
        return mat4.lookAt(
            mat4.create(),
            this.camera.position,
            this.camera.target,
            this.camera.up
        );
    }
    
    createProjectionMatrix() {
        const aspect = this.canvas.width / this.canvas.height;
        return mat4.perspective(mat4.create(), Math.PI / 4, aspect, 0.1, 100.0);
    }
    
    createNormalMatrix(modelMatrix) {
        const normalMatrix = mat3.create();
        mat3.fromMat4(normalMatrix, modelMatrix);
        mat3.invert(normalMatrix, normalMatrix);
        mat3.transpose(normalMatrix, normalMatrix);
        
        // Convert to mat4 for uniform
        const mat4Normal = mat4.create();
        mat4Normal[0] = normalMatrix[0];
        mat4Normal[1] = normalMatrix[1];
        mat4Normal[2] = normalMatrix[2];
        mat4Normal[4] = normalMatrix[3];
        mat4Normal[5] = normalMatrix[4];
        mat4Normal[6] = normalMatrix[5];
        mat4Normal[8] = normalMatrix[6];
        mat4Normal[9] = normalMatrix[7];
        mat4Normal[10] = normalMatrix[8];
        
        return mat4Normal;
    }
    
    showFallback() {
        // Create SVG fallback
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', '0 0 200 200');
        svg.style.position = 'absolute';
        svg.style.top = '0';
        svg.style.left = '0';
        
        // Create animated shield shape
        const shield = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        shield.setAttribute('d', 'M100 20 L160 60 L160 120 L100 180 L40 120 L40 60 Z');
        shield.setAttribute('fill', 'none');
        shield.setAttribute('stroke', '#00ffff');
        shield.setAttribute('stroke-width', '2');
        shield.setAttribute('opacity', '0.7');
        
        // Add glow filter
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'glow');
        const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur.setAttribute('stdDeviation', '3');
        filter.appendChild(feGaussianBlur);
        defs.appendChild(filter);
        svg.appendChild(defs);
        
        shield.style.filter = 'url(#glow)';
        shield.style.animation = 'pulse 2s ease-in-out infinite';
        
        svg.appendChild(shield);
        
        // Replace canvas with SVG
        this.canvas.style.display = 'none';
        this.canvas.parentNode.appendChild(svg);
        
        console.log('WebGL fallback: Using SVG shield');
    }
    
    // Public API methods
    setWireframe(enabled) {
        this.config.wireframe = enabled;
    }
    
    setShield(enabled) {
        this.config.shield = enabled;
    }
    
    setParticles(enabled) {
        this.config.particles = enabled;
    }
    
    setAutoRotate(enabled) {
        this.config.autoRotate = enabled;
    }
    
    setColors(neon, shield, particle) {
        if (neon) this.config.neonColor = neon;
        if (shield) this.config.shieldColor = shield;
        if (particle) this.config.particleColor = particle;
    }
    
    destroy() {
        // Clean up WebGL resources
        if (this.gl) {
            Object.values(this.programs).forEach(program => {
                this.gl.deleteProgram(program);
            });
            
            Object.values(this.buffers).forEach(bufferGroup => {
                Object.values(bufferGroup).forEach(buffer => {
                    if (buffer.deleteBuffer) {
                        this.gl.deleteBuffer(buffer);
                    }
                });
            });
        }
    }
}

// Basic matrix operations (simplified implementation)
const mat4 = {
    create: () => new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]),
    
    perspective: (out, fovy, aspect, near, far) => {
        const f = 1.0 / Math.tan(fovy / 2);
        out[0] = f / aspect;
        out[5] = f;
        out[10] = (far + near) / (near - far);
        out[11] = -1;
        out[14] = (2 * far * near) / (near - far);
        out[15] = 0;
        return out;
    },
    
    lookAt: (out, eye, center, up) => {
        let x0, x1, x2, y0, y1, y2, z0, z1, z2, len;
        
        if (Math.abs(eye[0] - center[0]) < 0.000001 &&
            Math.abs(eye[1] - center[1]) < 0.000001 &&
            Math.abs(eye[2] - center[2]) < 0.000001) {
            return mat4.create();
        }
        
        z0 = eye[0] - center[0];
        z1 = eye[1] - center[1];
        z2 = eye[2] - center[2];
        
        len = 1 / Math.sqrt(z0 * z0 + z1 * z1 + z2 * z2);
        z0 *= len;
        z1 *= len;
        z2 *= len;
        
        x0 = up[1] * z2 - up[2] * z1;
        x1 = up[2] * z0 - up[0] * z2;
        x2 = up[0] * z1 - up[1] * z0;
        len = Math.sqrt(x0 * x0 + x1 * x1 + x2 * x2);
        if (!len) {
            x0 = 0;
            x1 = 0;
            x2 = 0;
        } else {
            len = 1 / len;
            x0 *= len;
            x1 *= len;
            x2 *= len;
        }
        
        y0 = z1 * x2 - z2 * x1;
        y1 = z2 * x0 - z0 * x2;
        y2 = z0 * x1 - z1 * x0;
        
        out[0] = x0;
        out[1] = y0;
        out[2] = z0;
        out[3] = 0;
        out[4] = x1;
        out[5] = y1;
        out[6] = z1;
        out[7] = 0;
        out[8] = x2;
        out[9] = y2;
        out[10] = z2;
        out[11] = 0;
        out[12] = -(x0 * eye[0] + x1 * eye[1] + x2 * eye[2]);
        out[13] = -(y0 * eye[0] + y1 * eye[1] + y2 * eye[2]);
        out[14] = -(z0 * eye[0] + z1 * eye[1] + z2 * eye[2]);
        out[15] = 1;
        
        return out;
    },
    
    rotateX: (out, a, rad) => {
        const s = Math.sin(rad);
        const c = Math.cos(rad);
        out[5] = c;
        out[6] = s;
        out[9] = -s;
        out[10] = c;
        return out;
    },
    
    rotateY: (out, a, rad) => {
        const s = Math.sin(rad);
        const c = Math.cos(rad);
        out[0] = c;
        out[2] = -s;
        out[8] = s;
        out[10] = c;
        return out;
    },
    
    rotateZ: (out, a, rad) => {
        const s = Math.sin(rad);
        const c = Math.cos(rad);
        out[0] = c;
        out[1] = s;
        out[4] = -s;
        out[5] = c;
        return out;
    },
    
    scale: (out, a, v) => {
        out[0] = a[0] * v[0];
        out[5] = a[5] * v[1];
        out[10] = a[10] * v[2];
        return out;
    }
};

const mat3 = {
    create: () => new Float32Array([1,0,0,0,1,0,0,0,1]),
    
    fromMat4: (out, a) => {
        out[0] = a[0];
        out[1] = a[1];
        out[2] = a[2];
        out[3] = a[4];
        out[4] = a[5];
        out[5] = a[6];
        out[6] = a[8];
        out[7] = a[9];
        out[8] = a[10];
        return out;
    },
    
    invert: (out, a) => {
        const a00 = a[0], a01 = a[1], a02 = a[2];
        const a10 = a[3], a11 = a[4], a12 = a[5];
        const a20 = a[6], a21 = a[7], a22 = a[8];
        
        const b01 = a22 * a11 - a12 * a21;
        const b11 = -a22 * a10 + a12 * a20;
        const b21 = a21 * a10 - a11 * a20;
        
        let det = a00 * b01 + a01 * b11 + a02 * b21;
        
        if (!det) return null;
        
        det = 1.0 / det;
        
        out[0] = b01 * det;
        out[1] = (-a22 * a01 + a02 * a21) * det;
        out[2] = (a12 * a01 - a02 * a11) * det;
        out[3] = b11 * det;
        out[4] = (a22 * a00 - a02 * a20) * det;
        out[5] = (-a12 * a00 + a02 * a10) * det;
        out[6] = b21 * det;
        out[7] = (-a21 * a00 + a01 * a20) * det;
        out[8] = (a11 * a00 - a01 * a10) * det;
        
        return out;
    },
    
    transpose: (out, a) => {
        if (out === a) {
            const a01 = a[1], a02 = a[2], a12 = a[5];
            out[1] = a[3];
            out[2] = a[6];
            out[3] = a01;
            out[5] = a[7];
            out[6] = a02;
            out[7] = a12;
        } else {
            out[0] = a[0];
            out[1] = a[3];
            out[2] = a[6];
            out[3] = a[1];
            out[4] = a[4];
            out[5] = a[7];
            out[6] = a[2];
            out[7] = a[5];
            out[8] = a[8];
        }
        return out;
    }
};

// Export for global use
window.MatricaGlobe = MatricaGlobe;