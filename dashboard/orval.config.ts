import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: {
      target: "openapi.yaml",
    },
    output: {
      mode: "tags-split",
      client: "react-query",
      target: "src/api/endpoints",
      schemas: "src/api/models",
      override: {
        mutator: {
          path: "src/lib/api/client.ts",
          name: "axiosInstance",
        },
        query: {
          useQuery: true,
          useSuspenseQuery: true,
        },
      },
      clean: true,
      prettier: true,
    },
  },
});
