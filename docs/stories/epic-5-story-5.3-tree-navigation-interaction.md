# Story 5.3: Tree Navigation & Interaction

**Epic**: Epic 5 - Conversation Tree Visualization  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 8 hours

## Description

Add interactive navigation features to conversation tree: hover tooltips, expand/collapse subtrees, keyboard navigation, and smooth camera transitions when switching between conversations.

## Dependencies

**Blocks**:

- None (completes tree visualization feature)

**Requires**:

- Story 5.2: Conversation Tree Visualization Component (base tree component)

## Acceptance Criteria

- [ ] Hover tooltip shows: conversation title, message count, created date, creator
- [ ] Click node to navigate to that conversation with smooth camera transition
- [ ] Expand/collapse icons on nodes with children (▼/▶)
- [ ] Collapsed subtrees show badge: "+N more"
- [ ] Keyboard navigation: Arrow keys to move between nodes, Enter to select
- [ ] Breadcrumb trail above tree: Root → Parent → Current
- [ ] "Focus on current" button centers camera on active conversation
- [ ] Double-click node to expand/collapse its subtree
- [ ] Smooth transitions (300ms) on all interactions
- [ ] Tooltip follows cursor on hover
- [ ] Unit tests >80% coverage

## Technical Notes

**Enhanced Tree Component with Interactions**:

```vue
<template>
  <div class="conversation-tree-interactive">
    <!-- Breadcrumb Trail -->
    <div class="breadcrumb-trail">
      <span
        v-for="(ancestor, index) in activePath"
        :key="ancestor.id"
        class="breadcrumb-item"
        @click="navigateToNode(ancestor.id)"
      >
        {{ ancestor.title }}
        <ChevronRightIcon v-if="index < activePath.length - 1" />
      </span>
    </div>

    <div class="tree-controls">
      <button @click="focusOnCurrent" class="control-btn">
        <TargetIcon /> Focus on Current
      </button>
      <button @click="expandAll" class="control-btn">
        <ExpandIcon /> Expand All
      </button>
      <button @click="collapseAll" class="control-btn">
        <CollapseIcon /> Collapse All
      </button>
    </div>

    <svg
      ref="svgRef"
      class="tree-svg"
      @keydown="handleKeydown"
      tabindex="0"
    ></svg>

    <!-- Tooltip -->
    <div
      v-if="tooltipVisible"
      ref="tooltipRef"
      class="node-tooltip"
      :style="{ top: tooltipY + 'px', left: tooltipX + 'px' }"
    >
      <h4>{{ tooltipData.title }}</h4>
      <p><strong>Messages:</strong> {{ tooltipData.messageCount }}</p>
      <p v-if="tooltipData.forkMessageCount !== null">
        <strong>Forked from:</strong>
        {{ tooltipData.forkMessageCount }} messages
      </p>
      <p><strong>Created:</strong> {{ formatDate(tooltipData.createdAt) }}</p>
      <p><strong>By:</strong> @{{ tooltipData.createdBy }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import * as d3 from "d3";

const props = defineProps<{
  treeData: TreeNode;
  activeConversationId: string;
}>();

const emit = defineEmits(["node-click"]);

const svgRef = ref<SVGElement | null>(null);
const tooltipRef = ref<HTMLElement | null>(null);
const tooltipVisible = ref(false);
const tooltipX = ref(0);
const tooltipY = ref(0);
const tooltipData = ref<any>({});
const collapsedNodes = ref<Set<string>>(new Set());
const focusedNodeId = ref<string | null>(null);

let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
let g: d3.Selection<SVGGElement, unknown, null, undefined>;
let zoom: d3.ZoomBehavior<SVGSVGElement, unknown>;

const activePath = computed(() => {
  // Compute breadcrumb path from root to active conversation
  const path: TreeNode[] = [];
  const findPath = (node: TreeNode, targetId: string): boolean => {
    path.push(node);
    if (node.id === targetId) return true;

    if (node.children) {
      for (const child of node.children) {
        if (findPath(child, targetId)) return true;
      }
    }

    path.pop();
    return false;
  };

  findPath(props.treeData, props.activeConversationId);
  return path;
});

onMounted(() => {
  initializeInteractiveTree();
});

const initializeInteractiveTree = () => {
  const width = svgRef.value!.clientWidth;
  const height = svgRef.value!.clientHeight;

  svg = d3.select(svgRef.value!).attr("width", width).attr("height", height);

  zoom = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.5, 3])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svg.call(zoom);

  g = svg.append("g").attr("transform", `translate(${width / 2}, 50)`);

  renderInteractiveTree();
};

const renderInteractiveTree = () => {
  g.selectAll("*").remove();

  // Filter collapsed nodes
  const visibleTree = filterCollapsedNodes(props.treeData);

  const treeLayout = d3
    .tree<TreeNode>()
    .size([svgRef.value!.clientWidth - 200, svgRef.value!.clientHeight - 100]);

  const root = d3.hierarchy(visibleTree);
  const treeData = treeLayout(root);

  // Draw links
  g.selectAll(".link")
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
      if (event.detail === 2) {
        // Double-click: toggle expand/collapse
        toggleCollapse(d.data.id);
      } else {
        // Single-click: navigate
        emit("node-click", d.data.id);
      }
    })
    .on("mouseover", (event, d: any) => {
      showTooltip(event, d.data);
    })
    .on("mouseout", () => {
      hideTooltip();
    });

  // Node circles
  node
    .append("circle")
    .attr("r", 20)
    .attr("fill", (d: any) =>
      d.data.id === props.activeConversationId ? "#667eea" : "#e0e0e0"
    )
    .attr("stroke", (d: any) =>
      d.data.id === props.activeConversationId ? "#764ba2" : "#999"
    )
    .attr("stroke-width", (d: any) =>
      d.data.id === props.activeConversationId ? 3 : 1.5
    )
    .style("cursor", "pointer")
    .transition()
    .duration(300)
    .attr("r", 25);

  // Expand/collapse icons
  node
    .filter((d: any) => hasChildren(d.data))
    .append("text")
    .attr("dy", -35)
    .attr("text-anchor", "middle")
    .attr("font-size", "16px")
    .attr("cursor", "pointer")
    .text((d: any) => (collapsedNodes.value.has(d.data.id) ? "▶" : "▼"))
    .on("click", (event, d: any) => {
      event.stopPropagation();
      toggleCollapse(d.data.id);
    });

  // Collapsed badge (+N more)
  node
    .filter((d: any) => collapsedNodes.value.has(d.data.id))
    .append("circle")
    .attr("cy", 30)
    .attr("r", 15)
    .attr("fill", "#ff5722")
    .attr("stroke", "#fff")
    .attr("stroke-width", 2);

  node
    .filter((d: any) => collapsedNodes.value.has(d.data.id))
    .append("text")
    .attr("dy", 34)
    .attr("text-anchor", "middle")
    .attr("font-size", "10px")
    .attr("fill", "#fff")
    .attr("font-weight", "bold")
    .text((d: any) => `+${countDescendants(d.data)}`);
};

const filterCollapsedNodes = (node: TreeNode): TreeNode => {
  if (collapsedNodes.value.has(node.id)) {
    return { ...node, children: undefined };
  }

  if (node.children) {
    return {
      ...node,
      children: node.children.map(filterCollapsedNodes),
    };
  }

  return node;
};

const toggleCollapse = (nodeId: string) => {
  if (collapsedNodes.value.has(nodeId)) {
    collapsedNodes.value.delete(nodeId);
  } else {
    collapsedNodes.value.add(nodeId);
  }
  renderInteractiveTree();
};

const expandAll = () => {
  collapsedNodes.value.clear();
  renderInteractiveTree();
};

const collapseAll = () => {
  const collectNodeIds = (node: TreeNode): string[] => {
    const ids = [node.id];
    if (node.children) {
      node.children.forEach((child) => {
        ids.push(...collectNodeIds(child));
      });
    }
    return ids;
  };

  collectNodeIds(props.treeData).forEach((id) => {
    if (id !== props.treeData.id) {
      collapsedNodes.value.add(id);
    }
  });
  renderInteractiveTree();
};

const focusOnCurrent = () => {
  const activeNode = g
    .selectAll(".node")
    .filter((d: any) => d.data.id === props.activeConversationId);

  if (!activeNode.empty()) {
    const nodeData: any = activeNode.datum();
    const transform = d3.zoomIdentity
      .translate(svgRef.value!.clientWidth / 2 - nodeData.x, 150 - nodeData.y)
      .scale(1);

    svg.transition().duration(500).call(zoom.transform, transform);
  }
};

const showTooltip = (event: MouseEvent, data: TreeNode) => {
  tooltipData.value = data;
  tooltipVisible.value = true;
  tooltipX.value = event.pageX + 10;
  tooltipY.value = event.pageY + 10;
};

const hideTooltip = () => {
  tooltipVisible.value = false;
};

const handleKeydown = (event: KeyboardEvent) => {
  // Arrow key navigation
  const nodes = g.selectAll(".node").data();
  const currentIndex = nodes.findIndex(
    (d: any) => d.data.id === focusedNodeId.value
  );

  if (event.key === "ArrowDown" && currentIndex < nodes.length - 1) {
    focusedNodeId.value = (nodes[currentIndex + 1] as any).data.id;
  } else if (event.key === "ArrowUp" && currentIndex > 0) {
    focusedNodeId.value = (nodes[currentIndex - 1] as any).data.id;
  } else if (event.key === "Enter" && focusedNodeId.value) {
    emit("node-click", focusedNodeId.value);
  }
};

const hasChildren = (node: TreeNode): boolean => {
  return node.children !== undefined && node.children.length > 0;
};

const countDescendants = (node: TreeNode): number => {
  if (!node.children) return 0;
  return node.children.reduce((count, child) => {
    return count + 1 + countDescendants(child);
  }, 0);
};

const navigateToNode = (nodeId: string) => {
  emit("node-click", nodeId);
};

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};
</script>

<style scoped>
.conversation-tree-interactive {
  position: relative;
  width: 100%;
  height: 600px;
}

.breadcrumb-trail {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  padding: 8px 12px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.breadcrumb-item {
  font-size: 13px;
  color: #667eea;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.breadcrumb-item:hover {
  text-decoration: underline;
}

.node-tooltip {
  position: fixed;
  background: white;
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  pointer-events: none;
  max-width: 250px;
}

.node-tooltip h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

.node-tooltip p {
  margin: 4px 0;
  font-size: 12px;
  color: #666;
}

.tree-svg:focus {
  outline: 2px solid #667eea;
  outline-offset: -2px;
}
</style>
```

## QA Checklist

### Interactive Features

- [ ] Hover tooltip appears with conversation details
- [ ] Tooltip follows cursor smoothly
- [ ] Tooltip disappears on mouse leave
- [ ] Click node navigates to conversation
- [ ] Double-click toggles expand/collapse
- [ ] Expand/collapse icon (▼/▶) clickable
- [ ] Collapsed badge shows "+N more" correctly

### Navigation Features

- [ ] Breadcrumb trail shows path from root to active
- [ ] Breadcrumb items clickable to navigate
- [ ] "Focus on current" centers camera on active node
- [ ] Keyboard arrow keys navigate between nodes
- [ ] Enter key selects focused node
- [ ] Smooth transitions (300ms) on all interactions

### Expand/Collapse

- [ ] Expand All reveals entire tree
- [ ] Collapse All hides all subtrees except root
- [ ] Individual expand/collapse preserves other states
- [ ] Collapsed node count accurate
- [ ] Tree re-renders correctly after collapse/expand

### Performance

- [ ] Tooltip appears < 50ms on hover
- [ ] Camera transitions smooth (60 FPS)
- [ ] Expand/collapse renders < 200ms
- [ ] Keyboard navigation responsive < 100ms

### Accessibility

- [ ] Tooltip content announced to screen readers
- [ ] Keyboard focus visible on nodes
- [ ] ARIA labels on expand/collapse buttons
- [ ] Breadcrumb trail keyboard navigable

## Estimated Effort

8 hours
