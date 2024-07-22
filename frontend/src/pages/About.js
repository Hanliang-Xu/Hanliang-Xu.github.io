import React from 'react';
import './About.css';

const About = () => {
    return (
        <div className="about-container">
            <div className="about-left">
                <div className="about-header">
                    <h1>About</h1>
                    <div className="about-line"></div>
                </div>
            </div>
            <div className="about-right">
                <h2>I explore potentials of technologies to achieve social innovations.</h2>
                <p>I am:</p>
                <ul>
                    <li className="medium-font">a CS and Math major at Johns Hopkins University</li>
                    <li className="medium-font">a researcher in applying machine learning to medical image analysis</li>
                    <li className="medium-font">a software engineer for two organizations Book'em and OSIPI</li>
                    <li className="medium-font">a foil fencer, a history nerd, a learner</li>
                </ul>
            </div>
        </div>
    );
}

export default About;
