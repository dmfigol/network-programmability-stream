<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <p>
      Awesome network diagram based on graph data
    </p>
    <!-- Comment  <Network ref="network" :items="items" :groups="groups" :options="options" /> -->
    <d3-network :net-nodes="nodes" :net-links="links" :options="options" />
  </div>
</template>

<script>
// import Network from "vue-visjs";
// import { Network } from "vis-network";
// import { DataSet, DataView } from "vis-network";
import D3Network from "vue-d3-network";

export default {
  name: "NetworkDiagram",
  props: {
    msg: String,
  },
  components: {
    D3Network,
  },
  data: function() {
    return {
      count: 100,
      nodes: [
        { id: 1, name: "R1" },
        { id: 2, name: "R2" },
        { id: 3, _color: "R3" },
      ],
      links: [
        { sid: 1, tid: 2, _color: "red" },
        { sid: 2, tid: 8, _color: "f0f" },
        { sid: 3, tid: 4, _color: "rebeccapurple" },
        { sid: 4, tid: 5 },
        { sid: 5, tid: 6 },
        { sid: 7, tid: 8 },
        { sid: 5, tid: 8 },
        { sid: 3, tid: 8 },
        { sid: 7, tid: 9 },
      ],
      options: {
        force: 0,
        nodeSize: 20,
        nodeLabels: true,
        linkWidth: 5,
      },
    };
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style src="vue-d3-network/dist/vue-d3-network.css"></style>
<style></style>
