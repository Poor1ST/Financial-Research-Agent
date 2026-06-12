import { useTheme } from "../context/ThemeContext";

export default function ThemeToggle() {
  const { theme, toggle } = useTheme();

  return (
    <button
      className="theme-btn"
      onClick={toggle}
      title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
    >
      {theme === "dark" ? "\u2600\uFE0F" : "\u{1F319}"}
      <span style={{ fontSize: 13 }}>{theme === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
