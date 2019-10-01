CREATE DATABASE IF NOT EXISTS ApacheIssues;
USE ApacheIssues;

CREATE TABLE issues (
	BugId VARCHAR(50) NOT NULL,
    IssueType VARCHAR(50) NOT NULL,
    Severity VARCHAR(50) NOT NULL,
    DaysToClose DECIMAL(8,2) NOT NULL,
    NumComments INT NOT NULL,
    NumCommenters INT NOT NULL,
    Breaks VARCHAR(50) NOT NULL,
    IsBrokenBy VARCHAR(50) NOT NULL,
    PRIMARY KEY (BugID));
    