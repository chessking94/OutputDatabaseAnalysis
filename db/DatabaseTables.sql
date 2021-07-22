USE [ChessAnalysis]
GO
/****** Object:  Table [dbo].[ControlGames] ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ControlGames](
	[GameID] [int] IDENTITY(1,1) NOT NULL,
	[WhiteLast] [varchar](50) NOT NULL,
	[WhiteFirst] [varchar](30) NULL,
	[WhiteElo] [int] NULL,
	[BlackLast] [varchar](50) NOT NULL,
	[BlackFirst] [varchar](30) NULL,
	[BlackElo] [int] NULL,
	[ECO] [varchar](3) NULL,
	[GameDate] [datetime] NULL,
	[Tournament] [varchar](100) NULL,
	[RoundNum] [varchar](8) NULL,
	[Result] [decimal](2, 1) NULL,
	[Moves] [int] NULL,
	[DateAdded] [datetime] NULL,
	[CorrFlag] [tinyint] NULL,
 CONSTRAINT [PK_CG_GameID] PRIMARY KEY CLUSTERED 
(
	[GameID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ControlMoves] ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ControlMoves](
	[MoveID] [int] IDENTITY(1,1) NOT NULL,
	[GameID] [int] NOT NULL,
	[MoveNumber] [int] NOT NULL,
	[Color] [varchar](5) NOT NULL,
	[IsTheory] [tinyint] NULL,
	[IsTablebase] [tinyint] NULL,
	[Move] [varchar](10) NOT NULL,
	[T1] [varchar](10) NULL,
	[T2] [varchar](10) NULL,
	[T3] [varchar](10) NULL,
	[T4] [varchar](10) NULL,
	[T5] [varchar](10) NULL,
	[T6] [varchar](10) NULL,
	[T7] [varchar](10) NULL,
	[T8] [varchar](10) NULL,
	[T9] [varchar](10) NULL,
	[T10] [varchar](10) NULL,
	[T11] [varchar](10) NULL,
	[T12] [varchar](10) NULL,
	[T13] [varchar](10) NULL,
	[T14] [varchar](10) NULL,
	[T15] [varchar](10) NULL,
	[T16] [varchar](10) NULL,
	[T17] [varchar](10) NULL,
	[T18] [varchar](10) NULL,
	[T19] [varchar](10) NULL,
	[T20] [varchar](10) NULL,
	[T21] [varchar](10) NULL,
	[T22] [varchar](10) NULL,
	[T23] [varchar](10) NULL,
	[T24] [varchar](10) NULL,
	[T25] [varchar](10) NULL,
	[T26] [varchar](10) NULL,
	[T27] [varchar](10) NULL,
	[T28] [varchar](10) NULL,
	[T29] [varchar](10) NULL,
	[T30] [varchar](10) NULL,
	[T31] [varchar](10) NULL,
	[T32] [varchar](10) NULL,
	[Move_Eval] [varchar](6) NULL,
	[T1_Eval] [varchar](6) NULL,
	[T2_Eval] [varchar](6) NULL,
	[T3_Eval] [varchar](6) NULL,
	[T4_Eval] [varchar](6) NULL,
	[T5_Eval] [varchar](6) NULL,
	[T6_Eval] [varchar](6) NULL,
	[T7_Eval] [varchar](6) NULL,
	[T8_Eval] [varchar](6) NULL,
	[T9_Eval] [varchar](6) NULL,
	[T10_Eval] [varchar](6) NULL,
	[T11_Eval] [varchar](6) NULL,
	[T12_Eval] [varchar](6) NULL,
	[T13_Eval] [varchar](6) NULL,
	[T14_Eval] [varchar](6) NULL,
	[T15_Eval] [varchar](6) NULL,
	[T16_Eval] [varchar](6) NULL,
	[T17_Eval] [varchar](6) NULL,
	[T18_Eval] [varchar](6) NULL,
	[T19_Eval] [varchar](6) NULL,
	[T20_Eval] [varchar](6) NULL,
	[T21_Eval] [varchar](6) NULL,
	[T22_Eval] [varchar](6) NULL,
	[T23_Eval] [varchar](6) NULL,
	[T24_Eval] [varchar](6) NULL,
	[T25_Eval] [varchar](6) NULL,
	[T26_Eval] [varchar](6) NULL,
	[T27_Eval] [varchar](6) NULL,
	[T28_Eval] [varchar](6) NULL,
	[T29_Eval] [varchar](6) NULL,
	[T30_Eval] [varchar](6) NULL,
	[T31_Eval] [varchar](6) NULL,
	[T32_Eval] [varchar](6) NULL,
	[CP_Loss] [varchar](6) NULL,
	[Engine] [varchar](25) NULL,
	[Depth] [varchar](6) NULL,
	[AnalysisTime] [decimal](7, 4) NULL,
	[FEN] [varchar](92) NULL,
	[DateAdded] [datetime] NULL,
 CONSTRAINT [PK_CM_MoveID] PRIMARY KEY CLUSTERED 
(
	[MoveID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[ControlGames] ADD  DEFAULT (GETDATE()) FOR [DateAdded]
GO
ALTER TABLE [dbo].[ControlMoves] ADD  CONSTRAINT [CSR_CM_DateAdded]  DEFAULT (GETDATE()) FOR [DateAdded]
GO
ALTER TABLE [dbo].[ControlMoves]  WITH CHECK ADD  CONSTRAINT [FK_CM_GameID] FOREIGN KEY([GameID])
REFERENCES [dbo].[ControlGames] ([GameID])
GO
ALTER TABLE [dbo].[ControlMoves] CHECK CONSTRAINT [FK_CM_GameID]
GO
