# Story 5.2: Conversation Tree Visualization Component

**Epic**: Epic 5 - Conversation Tree Visualization  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 12 hours

## Description

Build D3.js-based interactive tree visualization component that renders conversation fork hierarchy with zoom, pan, and active path highlighting. Integrates with Vue 3 and supports mobile touch gestures.

## Dependencies

**Blocks**:

- Story 5.3: Tree Navigation & Interaction

**Requires**:

- Story 5.1: Conversation Tree Data Structure (tree API)
- Story 4.1: Conversation Data Model (conversation metadata)

## Acceptance Criteria

- [ ] `ConversationTreeViz.vue` component using D3.js v7
- [ ] Tree layout using `d3.tree()` with vertical orientation (root at top)
- [ ] Nodes display: conversation title, message count, fork_message_count badge
- [ ] Active conversation highlighted with distinct color/border
- [ ] Edges (links) show fork relationships
- [ ] Zoom controls: +/- buttons and mouse wheel (zoom range: 0.5x - 3x)
- [ ] Pan with mouse drag or touch gestures
- [ ] Smooth transitions on tree expand/collapse
- [ ] Responsive: Auto-resize on window resize
- [ ] Mobile-friendly: Touch zoom/pan gestures
- [ ] Export tree as PNG image
- [ ] Unit tests >80% coverage

## Technical Notes

**D3.js Tree Visualization Component**:

```vue
<template>
  <div class="conversation-tree-viz">
    <div class="tree-controls">
      <button @click="zoomIn" class="control-btn"><PlusIcon /> Zoom In</button>
      <button @click="zoomOut" class="control-btn">
        <MinusIcon /> Zoom Out
      </button>
      <button @click="resetView" class="control-btn">
        <ResetIcon /> Reset View
      </button>
      <button @click="exportImage" class="control-btn">
        <DownloadIcon /> Export PNG
      </button>
    </div>

    <svg ref="svgRef" class="tree-svg"></svg>

    <div v-if="isLoading" class="loading-overlay">
      <Spinner /> Loading conversation tree...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import * as d3 from "d3";

interface TreeNode {
  id: string;
  title: string;
  messageCount: number;
  forkMessageCount: number | null;
  isActive: boolean;
  children?: TreeNode[];
}

const props = defineProps<{
  treeData: TreeNode;
  activeConversationId: string;
}>();

const emit = defineEmits(["node-click"]);

const svgRef = ref<SVGElement | null>(null);
const isLoading = ref(false);

let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
let g: d3.Selection<SVGGElement, unknown, null, undefined>;
let zoom: d3.ZoomBehavior<SVGSVGElement, unknown>;

onMounted(() => {
  initializeTree();
});

watch(
  () => props.treeData,
  () => {
    renderTree();
  }
);

watch(
  () => props.activeConversationId,
  () => {
    highlightActivePath();
  }
);

const initializeTree = () => {
  const width = svgRef.value!.clientWidth;
  const height = svgRef.value!.clientHeight;

  // Initialize SVG
  svg = d3.select(svgRef.value!).attr("width", width).attr("height", height);

  // Create zoom behavior
  zoom = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.5, 3])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svg.call(zoom);

  // Create main group for tree
  g = svg.append("g").attr("transform", `translate(${width / 2}, 50)`);

  renderTree();
};

const renderTree = () => {
  if (!props.treeData) return;

  // Clear existing tree
  g.selectAll("*").remove();

  // Create tree layout
  const treeLayout = d3
    .tree<TreeNode>()
    .size([svgRef.value!.clientWidth - 200, svgRef.value!.clientHeight - 100])
    .separation((a, b) => (a.parent === b.parent ? 1 : 1.5));

  // Convert tree data to hierarchy
  const root = d3.hierarchy(props.treeData);
  const treeData = treeLayout(root);

  // Draw links (edges)
  const link = g
    .selectAll(".link")
    .data(treeData.links())
    .enter()
    .append("path")
    .attr("class", "link")
    .attr(
      "d",
      d3
        .linkVertical()
        .x((d: any) => d.x)
        .y((d: any) => d.y)
    )
    .attr("fill", "none")
    .attr("stroke", "#ccc")
    .attr("stroke-width", 2);

  // Draw nodes
  const node = g
    .selectAll(".node")
    .data(treeData.descendants())
    .enter()
    .append("g")
    .attr("class", "node")
    .attr("transform", (d: any) => `translate(${d.x}, ${d.y})`)
    .on("click", (event, d: any) => {
      emit("node-click", d.data.id);
    });

  // Node circles
  node
    .append("circle")
    .attr("r", 20)
    .attr("fill", (d: any) => (d.data.isActive ? "#667eea" : "#e0e0e0"))
    .attr("stroke", (d: any) => (d.data.isActive ? "#764ba2" : "#999"))
    .attr("stroke-width", (d: any) => (d.data.isActive ? 3 : 1.5))
    .style("cursor", "pointer")
    .transition()
    .duration(300)
    .attr("r", 25);

  // Node labels (conversation title)
  node
    .append("text")
    .attr("dy", 45)
    .attr("text-anchor", "middle")
    .attr("font-size", "12px")
    .attr("fill", "#333")
    .text((d: any) => truncate(d.data.title, 20));

  // Message count badge
  node
    .append("text")
    .attr("dy", 5)
    .attr("text-anchor", "middle")
    .attr("font-size", "10px")
    .attr("fill", "#fff")
    .attr("font-weight", "bold")
    .text((d: any) => d.data.messageCount);

  // Fork message count badge (if forked)
  node
    .filter((d: any) => d.data.forkMessageCount !== null)
    .append("circle")
    .attr("cx", 20)
    .attr("cy", -20)
    .attr("r", 12)
    .attr("fill", "#ff9800")
    .attr("stroke", "#fff")
    .attr("stroke-width", 2);

  node
    .filter((d: any) => d.data.forkMessageCount !== null)
    .append("text")
    .attr("x", 20)
    .attr("y", -16)
    .attr("text-anchor", "middle")
    .attr("font-size", "9px")
    .attr("fill", "#fff")
    .attr("font-weight", "bold")
    .text((d: any) => `${d.data.forkMessageCount}`);
};

const highlightActivePath = () => {
  // Find active node and highlight path from root
  g.selectAll(".node circle")
    .transition()
    .duration(300)
    .attr("fill", (d: any) =>
      d.data.id === props.activeConversationId ? "#667eea" : "#e0e0e0"
    )
    .attr("stroke", (d: any) =>
      d.data.id === props.activeConversationId ? "#764ba2" : "#999"
    )
    .attr("stroke-width", (d: any) =>
      d.data.id === props.activeConversationId ? 3 : 1.5
    );
};

const zoomIn = () => {
  svg.transition().duration(300).call(zoom.scaleBy, 1.3);
};

const zoomOut = () => {
  svg.transition().duration(300).call(zoom.scaleBy, 0.7);
};

const resetView = () => {
  svg
    .transition()
    .duration(500)
    .call(
      zoom.transform,
      d3.zoomIdentity.translate(svgRef.value!.clientWidth / 2, 50)
    );
};

const exportImage = () => {
  const svgElement = svgRef.value!;
  const svgData = new XMLSerializer().serializeToString(svgElement);
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;
  const img = new Image();

  canvas.width = svgElement.clientWidth;
  canvas.height = svgElement.clientHeight;

  img.onload = () => {
    ctx.drawImage(img, 0, 0);
    canvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob!);
      const a = document.createElement("a");
      a.href = url;
      a.download = "conversation-tree.png";
      a.click();
      URL.revokeObjectURL(url);
    });
  };

  img.src =
    "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
};

const truncate = (text: string, maxLength: number): string => {
  return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
};
</script>

<style scoped>
.conversation-tree-viz {
  position: relative;
  width: 100%;
  height: 600px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.tree-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 8px;
  z-index: 10;
}

.control-btn {
  background: white;
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #f5f5f5;
  border-color: #999;
}

.tree-svg {
  width: 100%;
  height: 100%;
  background: #fafafa;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .conversation-tree-viz {
    height: 400px;
  }

  .tree-controls {
    flex-direction: column;
  }

  .control-btn {
    width: 100%;
  }
}
</style>
```

**Usage in Conversation Page**:

```vue
<template>
  <div class="conversation-page">
    <div class="conversation-content">
      <!-- Main conversation messages -->
    </div>

    <div class="tree-sidebar">
      <h3>Conversation Tree</h3>
      <ConversationTreeViz
        :treeData="conversationTree"
        :activeConversationId="currentConversationId"
        @node-click="navigateToConversation"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import ConversationTreeViz from "@/components/ConversationTreeViz.vue";
import api from "@/services/api";

const route = useRoute();
const router = useRouter();

const conversationTree = ref(null);
const currentConversationId = ref(route.params.id);

onMounted(async () => {
  await loadConversationTree();
});

const loadConversationTree = async () => {
  try {
    const response = await api.get(
      `/conversations/${currentConversationId.value}/tree`
    );
    conversationTree.value = response.data;
  } catch (error) {
    console.error("Failed to load conversation tree:", error);
  }
};

const navigateToConversation = (conversationId: string) => {
  router.push(`/conversations/${conversationId}`);
};
</script>
```

## QA Checklist

### Functional Testing

- [ ] Tree renders correctly from hierarchical data
- [ ] Active conversation highlighted with distinct styling
- [ ] Zoom in/out buttons work correctly
- [ ] Mouse wheel zoom functions
- [ ] Pan with mouse drag works smoothly
- [ ] Node click emits event with conversation ID
- [ ] Fork message count badge displays for forked conversations

### Visualization Quality

- [ ] Tree layout avoids node overlap
- [ ] Links (edges) render smoothly without crossing
- [ ] Node labels truncate long titles
- [ ] Transitions smooth and performant (60 FPS)
- [ ] Active path highlighted clearly
- [ ] Fork count badge positioned correctly

### Responsive & Mobile

- [ ] Tree auto-resizes on window resize
- [ ] Touch zoom gestures work on mobile
- [ ] Touch pan gestures work on mobile
- [ ] Controls accessible on mobile
- [ ] Tree readable on small screens (≥ 375px width)

### Performance

- [ ] Tree renders < 500ms for 50 nodes
- [ ] Zoom/pan smooth (60 FPS)
- [ ] No memory leaks on component unmount
- [ ] Export PNG completes < 2 seconds

### Accessibility

- [ ] Keyboard navigation (Tab through nodes)
- [ ] ARIA labels on controls
- [ ] Screen reader announces active conversation
- [ ] Focus visible on nodes

## Estimated Effort

12 hours
