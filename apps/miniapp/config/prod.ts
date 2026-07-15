import type { UserConfigExport } from '@tarojs/cli'

export default {
  env: {
    NODE_ENV: '"production"',
  },
  defineConstants: {
    API_BASE_URL: '"https://api.floodshield.example.com/api"',
  },
  mini: {},
  h5: {},
} satisfies UserConfigExport
