module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
  },
  extends: ["eslint:recommended", "prettier"],
  plugins: ["html"],
  overrides: [
    {
      files: ["**/*.html"],
      processor: "html/html",
    },
  ],
  globals: {
    Vue: "readonly",
  },
  ignorePatterns: ["dist/", "node_modules/"],
};
