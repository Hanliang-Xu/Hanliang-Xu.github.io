import About from '../components/About';
import styles from './page.module.css';

export default function Home() {
  return (
    <main className={styles.main}>
      <section id="about">
        <About />
      </section>
    </main>
  );
}
