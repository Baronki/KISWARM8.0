CREATE TABLE `files` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`fileName` varchar(255) NOT NULL,
	`fileKey` varchar(512) NOT NULL,
	`fileUrl` text NOT NULL,
	`contentType` varchar(100) NOT NULL DEFAULT 'application/octet-stream',
	`fileSize` int NOT NULL DEFAULT 0,
	`category` enum('document','image','video','archive','other') NOT NULL DEFAULT 'other',
	`description` text,
	`uploadedAt` timestamp NOT NULL DEFAULT (now()),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `files_id` PRIMARY KEY(`id`)
);
