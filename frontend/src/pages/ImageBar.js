import React from 'react';
import './ImageBar.css';

const images = [
    'below_about_1.jpeg',
    'below_about_2.jpg',
    'below_about_3.png',
    'below_about_4.jpeg',
    'below_about_5.jpeg',
    'below_about_6.jpeg'
];

const ImageBar = () => {
    return (
        <div className="image-bar-container">
            <div className="image-bar">
                {images.concat(images).map((image, index) => (
                    <img key={index} src={`/${image}`} alt={`Below About ${index + 1}`} className="image-item" />
                ))}
            </div>
        </div>
    );
};

export default ImageBar;
