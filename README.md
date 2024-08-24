## Introduction
**Project Title**: Automatic 'ASL Parameters' Generator from DICOM/BIDS Images for Scientific
Publications\
**Name**: Hanliang Xu\
**Email**: hxu110@jh.edu\
**GitHub**: github.com/Hanliang-Xu\
**Organization**: Open Science Initiative for Perfusion Imaging (OSIPI)\
**Mentors**: Jan Petr, David Thomas\
**Duration**: Google Summer of Code 2024\

## Project Overview
**Goal of the Project**: The primary objective of this project is to create a tool that
automatically extracts and generates 'ASL parameters' from DICOM and BIDS images. This tool is
designed to assist researchers in easily describing standardized imaging parameters in their
scientific publications.\
**Project Summary**: The project focuses on developing a backend for extracting image header
information and generating a report, along with a frontend interface for user interaction. The
generated output is intended to be directly usable in the Methods section of research papers and
as supplementary material.

## Goals and Objectives
Develop a backend system capable of reading metadata from DICOM and BIDS formats and extracting
relevant ASL parameters.\
Create a frontend interface that allows users to upload images and receive a formatted output.\
Ensure that the tool adheres to community-endorsed standards for imaging parameters.\
Integrate the backend and frontend for seamless user interaction.

## Work Done
### Key Accomplishments:
**Backend Development**: Implemented a backend system extracting parameter information from DICOM
and BIDS files. This involved reading the image files (asl.json, m0.json, asl_context.tsv, .nii.gz)
, extracting relevant parameters, and formatting them into a short text and a table suitable for
scientific publications.\
**Frontend Interface**: Designed and developed a frontend interface using React.js to allow users
to upload their images and receive the generated output.\
**Integration**: Successfully integrated the backend with the frontend of the Google Cloud Platform
, enabling users to interact with the tool through a web interface.\
### Technical Details:
**Backend**:\
Developed scripts to extract ASL parameters from asl.json, m0.json, asl_context.tsv, .nii.gz as
well as the DICOM header.\
Implemented checks for the validity of parameter values and consistency across different subjects
and sessions, flagging any discrepancies or errors.\
Structured the output to include one brief, one extended report for the Methods section, and a
table for supplementary materials.\
**Frontend**:\
Developed using React.js, ensuring the interface is intuitive and meets the needs of researchers.\
Implemented upload functionality for DICOM and BIDS files, with the backend processing the files
and generating reports.\
Integrated design feedback from mentors and users to improve usability.\
**Code Contributions**:\
Backend for DICOM header extraction and ASL parameter generation:
[github.com/Hanliang-Xu/Hanliang-Xu.github.io/tree/main/backend](github.com/Hanliang-Xu/Hanliang-Xu.github.io/tree/main/backend)\
Frontend interface for user interaction: [github.com/Hanliang-Xu/Hanliang-Xu.github.io/tree/main/frontend](github.com/Hanliang-Xu/Hanliang-Xu.github.io/tree/main/frontend)\
**Pending Work**:\
Some features, such as integration of the docker version of dim2niix for cloud platform, were
not implemented due to time constraints. Noteworthy, these features were not mandatory
deliverables and were not part of the original specification either. 

## Current State of the Project
**Overall Status**:\
All goals that were in the original project proposal were achieved, and during my work, several
ideas came up that could further improve my work.\
**Completed Features**:\
Full implementation of the backend extraction tool for DICOM and BIDS formats.\
Functional frontend interface for user interaction.\
End-to-end integration allowing users to generate and download ASL parameters.\
**In Progress**:\
Finalizing documentation and addressing minor bugs.\
Additional enhancements suggested by mentors and users.\

## Future Work and What's Left to Do
**Remaining Tasks**:\
Complete documentation for future contributors.\
**Future Plans**:\
Polish the frontend design based on further user feedback.\
Extend the backend to support additional imaging modalities (DCE) or parameters if needed.
Implement dcm2niix docker.

## Lessons Learned
**Technical Skills**:\
Gained experience in file processing, specifically with JSON files, and handling of research
metadata.\
Improved web development skills, particularly in integrating complex backend processes with
frontend interfaces.\
Learned about the ASL perfusion MRI parameters.\
**Personal Growth**:\
Enhanced project management and time management skills, balancing multiple research commitments.\
Developed strong communication skills, particularly in collaborating with mentors and integrating
feedback into the project.\
**Project Management**:\
Learned the importance of iterative development and continuous feedback in producing a tool that
meets user needs.

## Acknowledgments
**Mentors**: Deep gratitude to Jan Petr and David Thomas for their guidance, feedback, and support
throughout the project.\
**Community**: Thanks to the OSIPI community for their collaboration and support, and to all those
who contributed feedback during the development process.\
**Organization**: Sincere thanks to OSIPI and Google Summer of Code for providing this opportunity
to contribute to the field of medical imaging.

## Conclusion
**Summary**: The project successfully developed an automatic “ASL parameters” generator that
extracts and formats key imaging parameters from DICOM and BIDS images. This tool will aid
researchers in standardizing their publications, contributing to the broader goal of harmonization
in perfusion MRI studies.\
**Final Thoughts**: This project has been an enriching experience, combining my passion for medical
imaging with practical software development. I look forward to continuing my contributions to OSIPI
and further exploring the exciting field of medical image processing.