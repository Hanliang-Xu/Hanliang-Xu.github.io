// Experience.js
import React from 'react';
import './Experience.css';

const Experience = () => {
    return (
        <div className="container">
            <h2>My Experience</h2>

            <div className="experience-item">
                <p>Research Engineer, Medical-image Analysis and Statistical Interpretation Lab</p>
                <a href="https://www.dropbox.com/scl/fi/r38hoe9597ecu4d5e4nn7/Hanliang_SPIE_8_pages.pdf?rlkey=mpucagha4b4aisz8vat5raju7&dl=0">
                    Link to my paper
                </a>
            </div>
            <br/>

            <div className="experience-item">
                <p>Web Developer, Generation Rise</p>
                <div className="img-container">
                    <div>
                        <img src="Generation_Rise.png" alt="Generation Rise"/>
                        <p>Description of my role</p>
                    </div>
                    <div>
                        <img src="Page_Sample.png" alt="Page Sample"/>
                        <p>The contact page I coded</p>
                    </div>
                </div>
            </div>
            <br/>

            <div className="experience-item">
                <p>Web Developer, Book'em as member in Change++</p>
                <p>We're still developing our portals!</p>
                <a href="https://www.changeplusplus.org/">
                    Link to Change++, Vanderbilt's most selective web dev student organization
                </a>
            </div>
        </div>
    );
}

export default Experience;
