DECLARE @err_ct int

EXEC dbo.DeleteStagedGameData @errors = 0

--stage games
TRUNCATE TABLE stage.games

INSERT INTO stage.Games (
	SourceName,
	SiteName,
	SiteGameID,
	WhiteLast,
	BlackLast,
	WhiteElo,
	BlackElo,
	TimeControlDetail,
	ECO_Code,
	GameDate,
	GameTime,
	EventName,
	Result
)

SELECT
'Lichess',
'Lichess',
GameID,
White,
Black,
WhiteElo,
BlackElo,
TimeControl,
ECO,
UTCDate,
UTCTime,
Event,
Result

FROM ChessAnalysis..LichessGames

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
		Clock,
		TimeSpent,
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
		T5_Eval
	)

	SELECT
	GameID,
	MoveNumber,
	Color,
	IsTheory,
	IsTablebase,
	Engine,
	Depth,
	Clock,
	TimeSpent,
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
	T5_Eval

	FROM ChessAnalysis..LichessMoves

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
