<template>
  <div>
    <h1>Network Diagram</h1>
    <network
      class="diagram"
      ref="network"
      :nodes="nodes"
      :edges="edges"
      :options="options"
    />
  </div>
</template>

<script>
import { Network } from "vue-visjs";

export default {
  name: "NetworkDiagram",
  components: {
    // Timeline,
    // DataSet,
    Network,
  },
  data: function() {
    return {
      count: 200,
      nodes: [
        {
          id: 1,
          label: "R1",
        },
        {
          id: 2,
          label: "R2",
        },
        {
          id: 3,
          label: "R3",
        },
        {
          id: 4,
          label: "R4",
        },
        {
          id: 5,
          label: "R5",
        },
        {
          id: 6,
          label: "R6",
        },
        {
          id: 7,
          label: "R7",
        },
        {
          id: 8,
          label: "R8",
        },
        {
          id: 9,
          label: "R9",
        },
        {
          id: 10,
          label: "R10",
        },
        {
          id: 11,
          label: "R11",
        },
        {
          id: 12,
          label: "R12",
        },
        {
          id: 13,
          label: "R13",
        },
        {
          id: 14,
          label: "R14",
        },
        {
          id: 15,
          label: "R15",
        },
      ],
      edges: [
        {
          from: 1,
          to: 2,
          title: "R1:g0/1 <-> R2:g0/1",
        },
        {
          from: 1,
          to: 2,
          title: "R1:g0/2 <-> R2:g0/2",
        },
        {
          from: 1,
          to: 3,
        },
        {
          from: 1,
          to: 3,
        },
        {
          from: 2,
          to: 4,
        },
        {
          from: 2,
          to: 5,
        },
        {
          from: 3,
          to: 6,
        },
        {
          from: 3,
          to: 7,
        },
        {
          from: 4,
          to: 8,
        },
        {
          from: 4,
          to: 9,
        },
        {
          from: 5,
          to: 10,
        },
        {
          from: 5,
          to: 11,
        },
        {
          from: 6,
          to: 12,
        },
        {
          from: 6,
          to: 13,
        },
        {
          from: 7,
          to: 14,
        },
        {
          from: 7,
          to: 15,
        },
      ],
      options: {
        layout: {
          randomSeed: 10,
        },
        physics: {
          enabled: true,
          // barnesHut: {
          //   springConstant: 0.9,
          //   avoidOverlap: 10
          // },
          // maxVelocity: 1,
          // minVelocity: 10,
          // solver: "barnesHut",
          // stabilization: {
          //   enabled: true,
          //   iterations: 1,
          //   onlyDynamicEdges: true,
          //   fit: true
          // },
          // timestep: 0.5,
          // adaptiveTimestep: true
        },
        interaction: {
          dragNodes: true,
        },
        stabilization: false,
        hierarchical: {
          enabled: true,
          // levelSeparation: 300, // does not seem to work, 150 default
          // nodeSpacing: 250, // 100 default
          direction: "UD", // UD, DU, LR, RL
          sortMethod: "directed", // hubsize, directed
        },
      },
    };
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<!-- <style src="vis-timeline/dist/vis-timeline-graph2d.css"></style> -->
<style scoped lang="scss">
.diagram {
  height: 800px;
}
</style>
