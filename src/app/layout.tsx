import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import Link from 'next/link';

import Providers from './providers';
import ThemeToggle from '../components/ThemeToggle';
import styles from './layout.module.css';
import './globals.css';

export const metadata: Metadata = {
  title: 'Hanliang Xu',
  description: 'Personal site of Hanliang Xu',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>
          <div className={styles.shell}>
            <header className={styles.topRow}>
              <div className={styles.left}>
                <h1 className={styles.name}>Hanliang Xu (Leon)</h1>
                <ThemeToggle />
              </div>

              <nav className={styles.nav}>
                <Link className={styles.navLink} href="/blog">
                  Blog
                </Link>
                <Link className={styles.navLink} href="/reading">
                  Reading
                </Link>
                <Link className={styles.navLink} href="/bookmarks">
                  Bookmarks
                </Link>
                <Link className={styles.navLink} href="/about">
                  About
                </Link>
              </nav>
            </header>
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
