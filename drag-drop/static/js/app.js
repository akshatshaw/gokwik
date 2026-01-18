// ===========================================
// State Management
// ===========================================
let connections = []; // Array of {fromNode, toNode}
let isDraggingNode = false;
let isDraggingConnection = false;
let currentNode = null;
let dragStartPort = null;
let mouseX = 0;
let mouseY = 0;
let offsetX = 0;
let offsetY = 0;
let selectedTool = 'duckduckgo';
let systemPrompt = "You are a helpful assistant that provides clear, concise summaries. Keep your response under 200 words.";
let selectedModel = 'gpt-3.5-turbo';

// ===========================================
// DOM Elements
// ===========================================
const canvas = document.getElementById('canvas');
const canvasArea = document.querySelector('.canvas-area');
const svg = document.getElementById('connectionSvg');
const toolNode1 = document.getElementById('toolNode1');
const toolNode2 = document.getElementById('toolNode2');
const agentNode = document.getElementById('agentNode');
const runBtn = document.getElementById('runBtn');
const disconnectBtn = document.getElementById('disconnectBtn');
const outputBox = document.getElementById('outputBox');
const userInput = document.getElementById('userInput');
const statusDot = document.querySelector('.status-dot');
const statusText = document.getElementById('statusText');
const modalOverlay = document.getElementById('modalOverlay');
const systemPromptInput = document.getElementById('systemPrompt');
const toolOptions = document.querySelectorAll('.tool-option');

// ===========================================
// Initialization
// ===========================================
function init() {
  initNodeDrag();
  initPortConnections();
  initAgentClick();
  initToolSelection();
  initModal();
  updateStatus();
  
  window.addEventListener('resize', redrawConnections);
  
  // Set initial system prompt
  systemPromptInput.value = systemPrompt;
}

// ===========================================
// Node Dragging
// ===========================================
function initNodeDrag() {
  const nodes = [toolNode1, toolNode2, agentNode];
  
  nodes.forEach(node => {
    node.addEventListener('mousedown', handleNodeMouseDown);
  });
  
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
}

function handleNodeMouseDown(e) {
  // Don't drag if clicking on port or agent body (for modal)
  if (e.target.classList.contains('connection-port')) {
    return;
  }
  
  currentNode = e.currentTarget;
  isDraggingNode = true;
  
  const rect = currentNode.getBoundingClientRect();
  const canvasRect = canvasArea.getBoundingClientRect();
  
  offsetX = e.clientX - rect.left;
  offsetY = e.clientY - rect.top;
  
  currentNode.classList.add('dragging');
  e.preventDefault();
}

function handleMouseMove(e) {
  mouseX = e.clientX;
  mouseY = e.clientY;
  
  if (isDraggingNode && currentNode) {
    const canvasRect = canvasArea.getBoundingClientRect();
    
    let x = e.clientX - canvasRect.left - offsetX;
    let y = e.clientY - canvasRect.top - offsetY;
    
    // Boundary constraints
    x = Math.max(10, Math.min(x, canvasRect.width - currentNode.offsetWidth - 10));
    y = Math.max(10, Math.min(y, canvasRect.height - currentNode.offsetHeight - 10));
    
    currentNode.style.left = x + 'px';
    currentNode.style.top = y + 'px';
    
    redrawConnections();
  }
  
  if (isDraggingConnection && dragStartPort) {
    drawTempConnection(e);
  }
}

function handleMouseUp(e) {
  if (currentNode) {
    currentNode.classList.remove('dragging');
  }
  
  if (isDraggingConnection) {
    finishConnection(e);
  }
  
  isDraggingNode = false;
  currentNode = null;
}

// ===========================================
// Port Connection (Drag to Connect)
// ===========================================
function initPortConnections() {
  const outputPorts = document.querySelectorAll('.output-port');
  const inputPorts = document.querySelectorAll('.input-port');
  
  outputPorts.forEach(port => {
    port.addEventListener('mousedown', startConnection);
  });
  
  inputPorts.forEach(port => {
    port.addEventListener('mouseup', completeConnection);
    port.addEventListener('mouseenter', highlightPort);
    port.addEventListener('mouseleave', unhighlightPort);
  });
}

function startConnection(e) {
  e.stopPropagation();
  e.preventDefault();
  
  isDraggingConnection = true;
  dragStartPort = e.currentTarget;
  dragStartPort.classList.add('active');
  
  // Create temp line
  drawTempConnection(e);
}

function drawTempConnection(e) {
  // Remove existing temp line
  const existingTemp = svg.querySelector('.temp-line');
  if (existingTemp) existingTemp.remove();
  
  const startRect = dragStartPort.getBoundingClientRect();
  const canvasRect = canvasArea.getBoundingClientRect();
  
  const x1 = startRect.left - canvasRect.left + startRect.width / 2;
  const y1 = startRect.top - canvasRect.top + startRect.height / 2;
  const x2 = e.clientX - canvasRect.left;
  const y2 = e.clientY - canvasRect.top;
  
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  const curve = Math.min(Math.abs(x2 - x1) * 0.5, 80);
  const d = `M ${x1} ${y1} C ${x1 + curve} ${y1}, ${x2 - curve} ${y2}, ${x2} ${y2}`;
  
  path.setAttribute('d', d);
  path.setAttribute('class', 'connection-line drawing temp-line');
  svg.appendChild(path);
}

function completeConnection(e) {
  if (!isDraggingConnection || !dragStartPort) return;
  
  const targetPort = e.currentTarget;
  const fromNode = dragStartPort.closest('.node');
  const toNode = targetPort.closest('.node');
  
  // Validate connection (tool to agent only)
  if (fromNode.dataset.type === 'tool' && toNode.dataset.type === 'agent') {
    // Check if this tool is already connected
    const existingIdx = connections.findIndex(c => c.fromNode === fromNode.id);
    if (existingIdx >= 0) {
      connections.splice(existingIdx, 1);
    }
    
    // Remove any other connection to agent (only one tool at a time)
    connections = connections.filter(c => c.toNode !== toNode.id);
    
    // Add new connection
    connections.push({
      fromNode: fromNode.id,
      toNode: toNode.id
    });
    
    // Update port styles
    updatePortStyles();
  }
}

function finishConnection(e) {
  // Clean up
  if (dragStartPort) {
    dragStartPort.classList.remove('active');
  }
  
  // Remove temp line
  const tempLine = svg.querySelector('.temp-line');
  if (tempLine) tempLine.remove();
  
  isDraggingConnection = false;
  dragStartPort = null;
  
  redrawConnections();
  updateStatus();
}

function highlightPort(e) {
  if (isDraggingConnection) {
    e.currentTarget.classList.add('active');
  }
}

function unhighlightPort(e) {
  if (!e.currentTarget.classList.contains('connected')) {
    e.currentTarget.classList.remove('active');
  }
}

function updatePortStyles() {
  // Reset all ports
  document.querySelectorAll('.connection-port').forEach(port => {
    port.classList.remove('connected');
  });
  
  // Mark connected ports
  connections.forEach(conn => {
    const fromNode = document.getElementById(conn.fromNode);
    const toNode = document.getElementById(conn.toNode);
    
    if (fromNode) {
      fromNode.querySelector('.output-port')?.classList.add('connected');
    }
    if (toNode) {
      toNode.querySelector('.input-port')?.classList.add('connected');
    }
  });
}

// ===========================================
// Connection Drawing
// ===========================================
function redrawConnections() {
  // Clear all except temp line
  const lines = svg.querySelectorAll('.connection-line:not(.temp-line)');
  lines.forEach(line => line.remove());
  
  connections.forEach(conn => {
    const fromNode = document.getElementById(conn.fromNode);
    const toNode = document.getElementById(conn.toNode);
    
    if (!fromNode || !toNode) return;
    
    const fromPort = fromNode.querySelector('.output-port');
    const toPort = toNode.querySelector('.input-port');
    
    if (!fromPort || !toPort) return;
    
    const canvasRect = canvasArea.getBoundingClientRect();
    const fromRect = fromPort.getBoundingClientRect();
    const toRect = toPort.getBoundingClientRect();
    
    const x1 = fromRect.left - canvasRect.left + fromRect.width / 2;
    const y1 = fromRect.top - canvasRect.top + fromRect.height / 2;
    const x2 = toRect.left - canvasRect.left + toRect.width / 2;
    const y2 = toRect.top - canvasRect.top + toRect.height / 2;
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const curve = Math.min(Math.abs(x2 - x1) * 0.5, 80);
    const d = `M ${x1} ${y1} C ${x1 + curve} ${y1}, ${x2 - curve} ${y2}, ${x2} ${y2}`;
    
    path.setAttribute('d', d);
    path.setAttribute('class', 'connection-line connected');
    svg.appendChild(path);
  });
  
  updatePortStyles();
}

// ===========================================
// Status Update
// ===========================================
function updateStatus() {
  const isConnected = connections.length > 0;
  
  if (isConnected) {
    const conn = connections[0];
    const toolName = conn.fromNode === 'toolNode1' ? 'DuckDuckGo' : 'Wikipedia';
    statusDot.classList.add('connected');
    statusDot.classList.remove('disconnected');
    statusText.textContent = `${toolName} → Agent`;
    disconnectBtn.disabled = false;
    
    // Update selected tool based on connection
    selectedTool = conn.fromNode === 'toolNode1' ? 'duckduckgo' : 'wikipedia';
    updateToolSelection();
  } else {
    statusDot.classList.remove('connected');
    statusDot.classList.add('disconnected');
    statusText.textContent = 'Not Connected';
    disconnectBtn.disabled = true;
  }
}

// ===========================================
// Disconnect
// ===========================================
disconnectBtn.addEventListener('click', () => {
  connections = [];
  redrawConnections();
  updateStatus();
});

// ===========================================
// Tool Selection
// ===========================================
function initToolSelection() {
  toolOptions.forEach(option => {
    option.addEventListener('click', () => {
      const tool = option.dataset.tool;
      selectedTool = tool;
      
      // Update visual selection
      updateToolSelection();
      
      // Auto-connect if not connected
      const targetNode = tool === 'duckduckgo' ? 'toolNode1' : 'toolNode2';
      connections = [{
        fromNode: targetNode,
        toNode: 'agentNode'
      }];
      
      redrawConnections();
      updateStatus();
    });
  });
}

function updateToolSelection() {
  toolOptions.forEach(option => {
    if (option.dataset.tool === selectedTool) {
      option.classList.add('selected');
    } else {
      option.classList.remove('selected');
    }
  });
}

// ===========================================
// Agent Modal (System Prompt)
// ===========================================
function initAgentClick() {
  const agentBody = agentNode.querySelector('.node-body');
  const agentFooter = agentNode.querySelector('.node-footer');
  
  [agentBody, agentFooter].forEach(el => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      openModal();
    });
  });
}

function initModal() {
  const closeBtn = document.getElementById('modalClose');
  const cancelBtn = document.getElementById('modalCancel');
  const saveBtn = document.getElementById('modalSave');
  
  closeBtn.addEventListener('click', closeModal);
  cancelBtn.addEventListener('click', closeModal);
  saveBtn.addEventListener('click', saveAgentSettings);
  
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
      closeModal();
    }
  });
  
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
    }
  });
}

function openModal() {
  systemPromptInput.value = systemPrompt;
  document.getElementById('modelSelect').value = selectedModel;
  modalOverlay.classList.add('active');
  setTimeout(() => systemPromptInput.focus(), 100);
}

function closeModal() {
  modalOverlay.classList.remove('active');
}

function saveAgentSettings() {
  systemPrompt = systemPromptInput.value.trim() || "You are a helpful assistant.";
  selectedModel = document.getElementById('modelSelect').value;
  closeModal();
}

// ===========================================
// Run Workflow
// ===========================================
runBtn.addEventListener('click', async () => {
  const input = userInput.value.trim();
  
  if (!input) {
    showOutput('Please enter a query!', 'error');
    return;
  }
  
  // Determine which tool is connected
  let connectedTool = null;
  if (connections.length > 0) {
    connectedTool = connections[0].fromNode === 'toolNode1' ? 'duckduckgo' : 'wikipedia';
  }
  
  // Show loading
  outputBox.innerHTML = '⏳ Running workflow...';
  outputBox.className = 'output-box loading';
  runBtn.disabled = true;
  
  try {
    const response = await fetch('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_input: input,
        connected: connections.length > 0,
        tool: connectedTool,
        system_prompt: systemPrompt,
        model: selectedModel
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showOutput(data.output, 'success');
    } else {
      showOutput(data.output, 'error');
    }
  } catch (error) {
    showOutput(`Error: ${error.message}`, 'error');
  } finally {
    runBtn.disabled = false;
  }
});

function showOutput(text, type) {
  outputBox.innerHTML = text;
  outputBox.className = `output-box ${type}`;
}

// ===========================================
// Start
// ===========================================
init();
