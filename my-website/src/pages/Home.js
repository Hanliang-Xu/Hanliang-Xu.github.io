import React from 'react';
import Avatar from '@mui/material/Avatar';
import './Home.css';

const Home = () => {
  return (
    <div className="home-box">
      <div className="left-section">
        <div className="header">
          <span className="small-font">Hi, my name is</span>
          <h1>Hanliang Xu.</h1>
          <h2>I explore potentials of technologies to achieve social innovations.</h2>
        </div>
        <div className="content">
          <p>I am</p>
          <ul>
            <li className="medium-font">• a CS and Math major at Vanderbilt University</li>
            <li className="medium-font">• a researcher in applying machine learning to medical image analysis</li>
            <li className="medium-font">• a web developer for two organizations Book'em and Generation Rise</li>
            <li className="medium-font">• a foil fencer, a history nerd, a learner</li>
          </ul>
        </div>
      </div>
      <div className="right-section">
        <div className="avatar-box">
          <Avatar
            alt="Hanliang Xu"
            src="Hanliang_Xu_Portrait.jpg"
            sx={{ width: 400, height: 400 }}
          />
        </div>
      </div>
    </div>
  );
};

export default Home;