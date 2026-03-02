import Image from 'next/image';
import styles from './About.module.css';

export default function About() {
  return (
    <section className={styles.root}>
      <div className={styles.content}>
        <h2 className={styles.heading}>👋 Welcome to My Site!</h2>
        <p className={styles.muted}>I explore potentials of technologies to achieve social innovations.</p>
        <p className={styles.label}>I am:</p>
        <ul className={styles.list}>
          <li>a CS and Math major at Johns Hopkins University</li>
          <li>a researcher in applying machine learning to medical image analysis</li>
          <li>a software engineer for two organizations Book&apos;em and OSIPI</li>
          <li>a foil fencer, a history nerd, a learner</li>
        </ul>
      </div>
      <div className={styles.photoWrap}>
        <Image
          alt="Portrait of Me"
          className={styles.photo}
          height={280}
          priority
          src="/me.jpg"
          width={280}
        />
      </div>
    </section>
  );
}
