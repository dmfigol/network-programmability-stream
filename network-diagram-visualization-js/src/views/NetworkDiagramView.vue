<template>
  <div>
    <NetworkDiagram />
  </div>
</template>

<script>
// @ is an alias to /src
import NetworkDiagram from "@/components/NetworkDiagram.vue";

export default {
  name: "NetworkDiagramView",
  components: {
    NetworkDiagram,
  },
};
</script>
