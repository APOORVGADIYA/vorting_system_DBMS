module.exports = {
  content: ["./templates/*.{html,js}"], // Adjust the path to match your file structure
  theme: {
    extend: {
      colors: {
        violet: "#8F00FF",
        indigo: "#4B0082",
        blue: "#0000FF",
        green: "#00FF00",
        yellow: "#FFFF00",
        orange: "#FFA500",
        red: "#FF0000",
      },
      fontFamily: {
        jetbrains: ['"JetBrains Mono"', "monospace"],
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      "light",
      "dark",
      "cupcake",
      "bumblebee",
      "emerald",
      "corporate",
      "synthwave",
      "retro",
      "cyberpunk",
      "valentine",
      "halloween",
      "garden",
      "forest",
      "aqua",
      "lofi",
      "pastel",
      "fantasy",
      "wireframe",
      "black",
      "luxury",
      "dracula",
      "cmyk",
      "autumn",
      "business",
      "acid",
      "lemonade",
      "night",
      "coffee",
      "winter",
      "dim",
      "nord",
      "sunset",
      {
        dbms: {
          primary: "#b900ff",

          "primary-content": "#f2daff",

          secondary: "#00b36c",

          "secondary-content": "#000c04",

          accent: "#00c9ff",

          "accent-content": "#000f16",

          neutral: "#1b2024",

          "neutral-content": "#cccdce",

          "base-100": "#fffaf7",

          "base-200": "#ded9d7",

          "base-300": "#bdbab7",

          "base-content": "#161515",

          info: "#0082f8",

          "info-content": "#000615",

          success: "#628b00",

          "success-content": "#030700",

          warning: "#e46600",

          "warning-content": "#120300",

          error: "#ffa29c",

          "error-content": "#160a09",
        },
      },
    ],
  },
};
