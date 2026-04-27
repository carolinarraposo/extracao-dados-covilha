USE [SNCrawler]
GO

-- 1. Redes Sociais
-- Insira manualmente: 'Bluesky', 'Reddit', 'Facebook', 'GoogleNews', 'YouTube'
CREATE TABLE [dbo].[SocialNetwork](
	[SNetwork_ID] [int] IDENTITY(1,1) NOT NULL,
	[SNetwork_Name] [varchar](50) NOT NULL, 
	[EntryDate_SN] [datetime] DEFAULT GETDATE(),
	PRIMARY KEY (SNetwork_ID)
);

-- 2. Utilizadores / Canais (UserSN)
CREATE TABLE [dbo].[UserSN](
	[User_ID] [bigint] IDENTITY(1,1) NOT NULL,
	[Handle] [nvarchar](255) NULL,       -- Nome do Autor ou Nome do Canal (YouTube)
	[SNetwork_ID] [int] NULL,
	[EntryDate_U] [datetime] DEFAULT GETDATE(),
	PRIMARY KEY (User_ID),
	FOREIGN KEY ([SNetwork_ID]) REFERENCES [dbo].[SocialNetwork] ([SNetwork_ID])
);

-- 3. Tabela Principal de Conteúdo (Posts, Vídeos, Notícias)
CREATE TABLE [dbo].[Post](
	[Post_ID] [bigint] IDENTITY(1,1) NOT NULL,
	[Original_External_ID] [nvarchar](500) NULL, -- video_id, post_id, URI ou URL
	[User_ID] [bigint] NULL,                    -- FK para o autor/canal
	[SNetwork_ID] [int] NOT NULL,
	[CreatedAt] [datetime] NULL,                -- published_date ou created_time
	[Title] [nvarchar](max) NULL,               -- Título do vídeo ou da notícia
	[Content] [ntext] NULL,                     -- Descrição do vídeo ou texto do post
	[URL] [nvarchar](max) NULL,                 -- video_url ou link da notícia
	[ViewCount] [bigint] DEFAULT 0,             -- EXCLUSIVO YOUTUBE: número de visualizações
	[LikeCount] [bigint] DEFAULT 0,             -- likes ou upvotes
	[ReplyCount] [bigint] DEFAULT 0,            -- comments_count ou total de respostas
	[EntryDate_DB] [datetime] DEFAULT GETDATE(),
PRIMARY KEY CLUSTERED ([Post_ID] ASC)
);

-- 4. Tabela de Comentários e Respostas
CREATE TABLE [dbo].[Comment](
	[Comment_ID] [bigint] IDENTITY(1,1) NOT NULL,
	[Post_ID] [bigint] NOT NULL,                -- ID do Post/Vídeo de origem
	[External_Comment_ID] [nvarchar](500) NULL, -- comment_id do YouTube/FB
	[Parent_Comment_ID] [bigint] NULL,          -- PARA YOUTUBE: Se for uma resposta, aponta para o ID do comentário pai
	[Author_Handle] [nvarchar](255) NULL,       -- Nome de quem comentou
	[Comment_Text] [ntext] NULL,
	[Likes_Upvotes] [int] DEFAULT 0,
	[CreatedAt] [datetime] NULL,
PRIMARY KEY (Comment_ID),
FOREIGN KEY ([Post_ID]) REFERENCES [dbo].[Post] ([Post_ID]),
CONSTRAINT [FK_Comment_Parent] FOREIGN KEY ([Parent_Comment_ID]) REFERENCES [dbo].[Comment] ([Comment_ID])
);

-- Índices para performance
CREATE INDEX IX_OriginalID ON [dbo].[Post] (Original_External_ID);
CREATE INDEX IX_ExternalCommentID ON [dbo].[Comment] (External_Comment_ID);
GO