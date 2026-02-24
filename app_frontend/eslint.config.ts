// eslint.config.ts
import {globalIgnores} from 'eslint/config'
import {defineConfigWithVueTs, vueTsConfigs} from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

// To allow more languages other than `ts` in `.vue` files, uncomment the following lines:
// import { configureVueProject } from '@vue/eslint-config-typescript'
// configureVueProject({ scriptLangs: ['ts', 'tsx'] })
// More info at https://github.com/vuejs/eslint-config-typescript/#advanced-setup

export default defineConfigWithVueTs(
    {
      name: 'app/files-to-lint',
      files: ['**/*.{vue,ts,mts,tsx}'],
    },

    globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**']),

    ...pluginVue.configs['flat/essential'],
    vueTsConfigs.recommended,

    skipFormatting,
    {
      name: 'app/custom-rules',
      rules: {
        // 关闭 any 类型的警告
        '@typescript-eslint/no-explicit-any': 'off',

        // 关闭未使用变量的警告
        '@typescript-eslint/no-unused-vars': 'off',
        '@typescript-eslint/no-empty-object-type': 'off',

        // (可选) 如果你也想关闭 Vue 模板中未使用变量的检查
        'vue/no-unused-vars': 'off',

        // (可选) 如果你想关闭组件名必须多单词的限制
        'vue/multi-word-component-names': 'off'
      }
    }
)
