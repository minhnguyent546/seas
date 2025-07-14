import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  client: 'legacy/axios',
  input: 'http://localhost:8444/api/v1/openapi.json', // This should be changed later!
  output: './src/client',
  plugins: [
    {
      name: '@hey-api/sdk',
      // NOTE: this doesn't allow tree-shaking
      asClass: true,
      operationId: true,
      methodNameBuilder: (operation) => {
        // @ts-expect-error: operation.name is not typed
        let name: string = operation.name;
        // @ts-expect-error : operation.service is not typed
        const service: string = operation.service;

        if (service && name.toLowerCase().startsWith(service.toLowerCase())) {
          name = name.slice(service.length);
        }

        return name.charAt(0).toLowerCase() + name.slice(1);
      },
    },
  ],
});
