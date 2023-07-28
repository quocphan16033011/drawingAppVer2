// Class Draw
class Draw {
  constructor() {
    // Declare the card canvasGl - main draw
    this.canvas = document.querySelector('#canvasGL');
    this.canvas.width = document.getElementById("wrap_canvas_div").clientWidth;
    this.canvas.height = document.getElementById("wrap_canvas_div").clientHeight;
    this.gl = this.canvas.getContext('experimental-webgl');

    // Declare the card canvas2D - text value of color bar
    this.canvas_text = document.querySelector('#text_colorbar');
    this.canvas_text.width = 65;
    this.canvas_text.height = 400;
    this.ctx_gl = this.canvas_text.getContext('2d');

    // Declare the card canavasGL - color bar
    this.canvas_colorbar = document.querySelector('#canvas_colorbar');
    this.canvas_colorbar.width = 50;
    this.canvas_colorbar.height = 400;
    this.gl_colorbar = this.canvas_colorbar.getContext('webgl2');

    // Declare the vertex and fragment shader
    this.vertex_fill = this.loadVSFG('../frontend/shader/shader_fill.vs');
    this.fragment_fill = this.loadVSFG('../frontend/shader/shader_fill.fs');
    this.vertex_black = this.loadVSFG('../frontend/shader/shader_black.vs');
    this.fragment_black = this.loadVSFG('../frontend/shader/shader_black.fs');

    // Compiles shaders, links program
    this.programInfo = twgl.createProgramInfo(this.gl, [this.vertex_fill, this.fragment_fill]);
    this.programInfo_colorbar = twgl.createProgramInfo(this.gl_colorbar, [this.vertex_black, this.fragment_black]);
    this.programInfo_edges = twgl.createProgramInfo(this.gl, [this.vertex_black, this.fragment_black]);
    // Declare the geometry sphere imformation from library twgl
    this.sphereVerts = twgl.primitives.createSphereVertices(1, 24, 12);

    // Create the buffer info from array for the sphere geometry
    this.sphereBufferInfo = twgl.createBufferInfoFromArrays(this.gl, {
      a_position: this.sphereVerts.position,
      indices: this.sphereVerts.indices,
    });

    // Declare card filler to take the value to load the fillter model
    this.filter_value = document.getElementById("filter");

    // Create camera
    this.camera = {
      x: 0,
      y: 0,
      rotation: 0,
      zoom: 1,
    };

    // Declare scene view and set up mouse position
    this.viewProjectionMat = new Float32Array([0.0013840830652043223, 0, 0, 0, -0.004566209856420755, 0, -1, 1, 1]);
    this.viewProjectionMat_colorbar;
    this.startInvViewProjMat;
    this.startCamera;
    this.startPos;
    this.startClipPos;
    this.startMousePos;
    this.startInvViewProjMat_check;
    this.startCamera_check;
    this.startPos_check;
    this.startClipPos_check;
    this.startMousePos_check;

    //  Declare rotate
    this.rotate;

    // Declare nearpointGL to interesction check point near mouse
    this.nearPointGL;
    this.nearPointGL_storage;

    // Declare array to storage the data for drawing
    this.lineVertex = [];
    this.point_x = [];
    this.point_y = [];
    this.segment_mesh = [];
    this.segment_fill = [];
    this.segment = [];
    this.takePoint = [];
    this.fillcolor = [];
    this.colorbar_size = [];
    this.colorbar_indices = [];
    this.pointcheck = [];
    this.takevalueRange = [];
    this.scene = [];
    this.scene_fill = [];
    this.scene_color = [];
    this.scene_load = [];
    this.colorvec4 = [];
    this.color_black = [0, 0, 0, 1];
    this.color_red = [1, 0, 0, 1];
    this.color = [1,1,1,1];
  }
  
  // Load vertex and fragment shader
  loadVSFG(path) {
    var request = new XMLHttpRequest();
    request.open('GET', path, false);
    request.overrideMimeType('text\/plain; charset=x-user-defined');
    request.send();
    return ((request.status === 0) || (request.status === 200)) ? request.responseText : null;
  }

  // processing data matrix when zoom, move and rotate
  makeCameraMatrix() {
    const zoomScale = 1 / DrawGL.camera.zoom;
    let cameraMat = m3.identity();
    cameraMat = m3.translate(cameraMat, DrawGL.camera.x, DrawGL.camera.y);
    cameraMat = m3.rotate(cameraMat, DrawGL.camera.rotation);
    cameraMat = m3.scale(cameraMat, zoomScale, zoomScale);
    return cameraMat;
  }

  // update view scene when zoom, move and rotate
  updateViewProjection() {
    // same as ortho(0, width, height, 0, -1, 1)
    const projectionMat = m3.projection(this.gl.canvas.width, this.gl.canvas.height);
    const cameraMat = this.makeCameraMatrix();
    let viewMat = m3.inverse(cameraMat);
    DrawGL.viewProjectionMat = m3.multiply(projectionMat, viewMat);
  }

  // Draw check point
  drawCheckpoint(thing) {
    this.gl.useProgram(this.programInfo_edges.program);
    const { x, y,color, bufferInfo } = thing;
    twgl.setBuffersAndAttributes(this.gl, this.programInfo_edges, bufferInfo);
    let mat = m3.identity();
    mat = m3.translate(mat, x, y);
    mat = m3.rotate(mat, 0);
    mat = m3.scale(mat, 5 / DrawGL.camera.zoom, 5 / DrawGL.camera.zoom);
    this.gl.getParameter(this.gl.LINE_WIDTH);
    this.gl.getParameter(this.gl.ALIASED_LINE_WIDTH_RANGE);
    // calls gl.uniformXXX
    twgl.setUniforms(this.programInfo_edges, {
      u_matrix: m3.multiply(DrawGL.viewProjectionMat, mat),
      u_color: color,
    });
    // calls gl.drawArrays or gl.drawElements
    twgl.drawBufferInfo(this.gl, bufferInfo);
  }
  drawLoad() {
    this.gl.useProgram(this.programInfo_edges.program);
    for (let i = 0; i < DrawGL.scene_load.length; i++) {
      const { x, y, rotation, scale, bufferInfo } = DrawGL.scene_load[i];
      // calls gl.bindBuffer, gl.enableVertexAttribArray, gl.vertexAttribPointer
      twgl.setBuffersAndAttributes(this.gl, this.programInfo_edges, bufferInfo);
      let mat = m3.identity();
      mat = m3.translate(mat, x, y);
      mat = m3.rotate(mat, rotation);
      mat = m3.scale(mat, scale, scale);
      this.gl.getParameter(this.gl.LINE_WIDTH);
      this.gl.getParameter(this.gl.ALIASED_LINE_WIDTH_RANGE);
      // calls gl.uniformXXX
      twgl.setUniforms(this.programInfo_edges, {
        u_matrix: m3.multiply(DrawGL.viewProjectionMat, mat),
        u_color: DrawGL.color_black,
      });

      // calls gl.drawArrays or gl.drawElements
      twgl.drawBufferInfo(this.gl, bufferInfo, this.gl.LINES);
      twgl.drawBufferInfo(this.gl, bufferInfo, this.gl.POINTS);
    }
  }
  colorBar() {
    this.gl_colorbar.useProgram(this.programInfo_colorbar.program);
    for (let i = 0; i < DrawGL.scene_color.length; i++) {
      const { x, y, rotation, scale, color, bufferInfo } = DrawGL.scene_color[i];
      // calls gl.bindBuffer, gl.enableVertexAttribArray, gl.vertexAttribPointer
      twgl.setBuffersAndAttributes(this.gl_colorbar, this.programInfo_colorbar, bufferInfo);
      let mat = m3.identity();
      mat = m3.translate(mat, x, y);
      mat = m3.rotate(mat, rotation);
      mat = m3.scale(mat, scale, scale);
      this.gl_colorbar.getParameter(this.gl_colorbar.LINE_WIDTH);
      this. gl_colorbar.getParameter(this.gl_colorbar.ALIASED_LINE_WIDTH_RANGE);
      // calls gl.uniformXXX
      twgl.setUniforms(this.programInfo_colorbar, {
        u_matrix: new Float32Array([0.03999999910593033, 0, 0, 0, -0.004999999888241291, 0, -1, 1, 1]),
        u_color: color,
      });
      // calls gl.drawArrays or gl.drawElements
      twgl.drawBufferInfo(this.gl_colorbar, bufferInfo);
    }
  }
  fillColor() {
    for (let i = 0; i < DrawGL.scene_fill.length; i++) {
      const { x, y, rotation, scale, bufferInfo } = DrawGL.scene_fill[i];
      // calls gl.bindBuffer, gl.enableVertexAttribArray, gl.vertexAttribPointer
      twgl.setBuffersAndAttributes(this.gl, this.programInfo, bufferInfo);
      let mat = m3.identity();
      mat = m3.translate(mat, x, y);
      mat = m3.rotate(mat, rotation);
      mat = m3.scale(mat, scale, scale);
      this.gl.getParameter(this.gl.LINE_WIDTH);
      this.gl.getParameter(this.gl.ALIASED_LINE_WIDTH_RANGE);
      // calls gl.uniformXXX
      twgl.setUniforms(this.programInfo, {
        u_matrix: m3.multiply(DrawGL.viewProjectionMat, mat),
      });

      // calls gl.drawArrays or gl.drawElements
      twgl.drawBufferInfo(this.gl, bufferInfo);
    }
  }
  drawMesh() {
    for (let i = 0; i < DrawGL.scene.length; i++) {
      const { x, y, rotation, scale, bufferInfo } = DrawGL.scene[i];
      // calls gl.bindBuffer, gl.enableVertexAttribArray, gl.vertexAttribPointer
      twgl.setBuffersAndAttributes(this.gl, this.programInfo, bufferInfo);
      var color_default = [0, 0, 0, 1];
      let mat = m3.identity();
      mat = m3.translate(mat, x, y);
      mat = m3.rotate(mat, rotation);
      mat = m3.scale(mat, scale, scale);
      this.gl.getParameter(this.gl.LINE_WIDTH);
      this.gl.getParameter(this.gl.ALIASED_LINE_WIDTH_RANGE);
      // calls gl.uniformXXX
      twgl.setUniforms(this.programInfo, {
        u_matrix: m3.multiply(DrawGL.viewProjectionMat, mat),
        u_color: color_default,
      });

      // calls gl.drawArrays or gl.drawElements
      twgl.drawBufferInfo(this.gl, bufferInfo, this.gl.LINES);
    }
  }
  draw() {
    this.gl.clear(this.gl.COLOR_BUFFER_BIT);
    this.updateViewProjection();
    this.gl.useProgram(this.programInfo.program);
    if (document.getElementById("fillColor").value === "On") {
      this.canvas.addEventListener('pointermove', (e) => {
        // canvas.style.cursor = "url(frontend/img/select_cursor.svg) 0 0, default";
        this.canvas.style.cursor = "pointer";
      })
      this.canvas.addEventListener('pointermove', checkSolution)
      this.fillColor();
      this.drawMesh();
    } else if (document.getElementById("fillColor").value === "Off") {
      this.canvas.addEventListener('pointermove', (e) => {
        this.canvas.style.cursor = "url(frontend/img/select_cursor.svg) 0 0, default";
        // canvas.style.cursor = "pointer;
      })
      this.canvas.removeEventListener('pointermove', checkSolution)
      document.getElementById("property").style.display="none";
      this.fillColor();
    }
    this.drawLoad();
    DrawGL.drawCheckpoint({
      x: DrawGL.nearPointGL_storage[0].x,
      y: DrawGL.nearPointGL_storage[0].y,
      color : DrawGL.color,
      bufferInfo: DrawGL.sphereBufferInfo,
    });
  }
}

const DrawGL = new Draw();