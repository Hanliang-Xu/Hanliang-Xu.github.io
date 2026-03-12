'use client';

import { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import { Sun, Moon } from 'lucide-react';
import styles from './ThemeToggle.module.css';

export default function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const isDark = resolvedTheme === 'dark';

  return (
    <button
      aria-label="Toggle theme"
      className={styles.button}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      type="button"
    >
      {mounted ? (isDark ? <Sun size={20} /> : <Moon size={20} />) : <Moon size={20} />}
    </button>
  );
}
