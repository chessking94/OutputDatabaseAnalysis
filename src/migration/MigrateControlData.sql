DECLARE @err_ct int

EXEC dbo.DeleteStagedGameData @errors = 0

--stage games
TRUNCATE TABLE stage.games

INSERT INTO stage.Games (
	SourceName,
	SiteGameID,
	WhiteLast,
	WhiteFirst,
	BlackLast,
	BlackFirst,
	WhiteElo,
	BlackElo,
	TimeControlDetail,
	ECO_Code,
	GameDate,
	EventName,
	RoundNum,
	Result
)

SELECT
'Control',
GameID,
WhiteLast,
WhiteFirst,
BlackLast,
BlackFirst,
WhiteElo,
BlackElo,
CASE WHEN CorrFlag = 1 THEN '1/1209600' ELSE '5400+30' END,
ECO,
GameDate,
Tournament,
RoundNum,
Result

FROM ChessAnalysis..ControlGames

--format
EXEC dbo.FormatGameData

SELECT @err_ct = COUNT(Errors) FROM stage.Games WHERE Errors IS NOT NULL

IF @err_ct = 0
BEGIN
	--stage moves
	TRUNCATE TABLE stage.Moves

	INSERT INTO stage.Moves (
		SiteGameID,
		MoveNumber,
		Color,
		IsTheory,
		IsTablebase,
		EngineName,
		Depth,
		FEN,
		PhaseID,
		Move,
		Move_Eval,
		Move_Rank,
		CP_Loss,
		T1,
		T1_Eval,
		T2,
		T2_Eval,
		T3,
		T3_Eval,
		T4,
		T4_Eval,
		T5,
		T5_Eval,
		T6,
		T6_Eval,
		T7,
		T7_Eval,
		T8,
		T8_Eval,
		T9,
		T9_Eval,
		T10,
		T10_Eval,
		T11,
		T11_Eval,
		T12,
		T12_Eval,
		T13,
		T13_Eval,
		T14,
		T14_Eval,
		T15,
		T15_Eval,
		T16,
		T16_Eval,
		T17,
		T17_Eval,
		T18,
		T18_Eval,
		T19,
		T19_Eval,
		T20,
		T20_Eval,
		T21,
		T21_Eval,
		T22,
		T22_Eval,
		T23,
		T23_Eval,
		T24,
		T24_Eval,
		T25,
		T25_Eval,
		T26,
		T26_Eval,
		T27,
		T27_Eval,
		T28,
		T28_Eval,
		T29,
		T29_Eval,
		T30,
		T30_Eval,
		T31,
		T31_Eval,
		T32,
		T32_Eval
	)

	SELECT
	GameID,
	MoveNumber,
	Color,
	IsTheory,
	IsTablebase,
	Engine,
	ISNULL(NULLIF(Depth, 'TB'), 0),
	FEN,
	PhaseID,
	Move,
	Move_Eval,
	Move_Rank,
	CP_Loss,
	T1,
	T1_Eval,
	T2,
	T2_Eval,
	T3,
	T3_Eval,
	T4,
	T4_Eval,
	T5,
	T5_Eval,
	T6,
	T6_Eval,
	T7,
	T7_Eval,
	T8,
	T8_Eval,
	T9,
	T9_Eval,
	T10,
	T10_Eval,
	T11,
	T11_Eval,
	T12,
	T12_Eval,
	T13,
	T13_Eval,
	T14,
	T14_Eval,
	T15,
	T15_Eval,
	T16,
	T16_Eval,
	T17,
	T17_Eval,
	T18,
	T18_Eval,
	T19,
	T19_Eval,
	T20,
	T20_Eval,
	T21,
	T21_Eval,
	T22,
	T22_Eval,
	T23,
	T23_Eval,
	T24,
	T24_Eval,
	T25,
	T25_Eval,
	T26,
	T26_Eval,
	T27,
	T27_Eval,
	T28,
	T28_Eval,
	T29,
	T29_Eval,
	T30,
	T30_Eval,
	T31,
	T31_Eval,
	T32,
	T32_Eval

	FROM ChessAnalysis..ControlMoves

	EXEC dbo.FormatMoveData

	SELECT @err_ct = COUNT(Errors) FROM stage.Moves WHERE Errors IS NOT NULL

	IF @err_ct = 0
	BEGIN
		--stage new dimension data
		EXEC dbo.InsertNewEvents
		EXEC dbo.InsertNewPlayers
		EXEC dbo.InsertNewTimeControls

		--add new key values to staged game data
		EXEC dbo.UpdateStagedGameKeys

		--create new game records
		EXEC dbo.InsertNewGames

		--add new key values to staged move data
		EXEC dbo.UpdateStagedMoveKeys

		--create new move records
		EXEC dbo.InsertNewMoves
	END
END

EXEC dbo.DeleteStagedGameData @errors = @err_ct
