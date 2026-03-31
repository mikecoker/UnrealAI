#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "Engine/Blueprint.h"
#include "UnrealAIGraphLibrary.generated.h"

USTRUCT(BlueprintType)
struct FUnrealAINodeInfo
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="UnrealAI")
    FString NodeName;

    UPROPERTY(BlueprintReadOnly, Category="UnrealAI")
    FString NodeClass;

    UPROPERTY(BlueprintReadOnly, Category="UnrealAI")
    TArray<FString> InputPins;

    UPROPERTY(BlueprintReadOnly, Category="UnrealAI")
    TArray<FString> OutputPins;
};

UCLASS()
class UNREALAIBFL_API UUnrealAIGraphLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /**
     * Add a function call node to a Blueprint graph.
     * @param Graph      The target graph (from find_event_graph / find_graph).
     * @param FunctionPath  "ClassName:FunctionName" for native functions, or
     *                      "/Game/Path/To/BP.BP_C:FuncName" for Blueprint functions.
     * @param NodeX / NodeY  Position in graph canvas units.
     * @return The created node, or nullptr on failure.
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static UEdGraphNode* AddFunctionCallNode(
        UEdGraph* Graph,
        const FString& FunctionPath,
        float NodeX,
        float NodeY);

    /**
     * Connect two pins by node-name + pin-name strings.
     * Finds nodes within the graph by their object name.
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static bool ConnectGraphPins(
        UEdGraph* Graph,
        const FString& FromNodeName,
        const FString& FromPinName,
        const FString& ToNodeName,
        const FString& ToPinName);

    /**
     * Set the default value of a Blueprint member variable by name.
     * Value is always passed as a string (matches how UE stores defaults internally).
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Blueprint")
    static bool SetVariableDefaultValue(
        UBlueprint* Blueprint,
        const FString& VariableName,
        const FString& DefaultValue);

    /**
     * Return info about all nodes in a graph (names, pin names).
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static TArray<FUnrealAINodeInfo> GetGraphNodes(UEdGraph* Graph);

    /** List all member variable names on a Blueprint (for debugging). */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Blueprint")
    static TArray<FString> GetVariableNames(UBlueprint* Blueprint);

    /**
     * Return the event function name for a K2Node_Event node by its object name.
     * Returns empty string if the node is not found or not an event node.
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static FString GetEventNodeFunctionName(UEdGraph* Graph, const FString& NodeName);

    /**
     * Add (or find existing) an event override node for a named event.
     * EventName: "Tick", "BeginPlay", "EndPlay", "ActorBeginOverlap", etc.
     * Searches the Blueprint's class hierarchy for the matching function.
     * Returns the existing node if already present, otherwise creates it.
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static UEdGraphNode* AddOrFindEventNode(
        UEdGraph* Graph,
        UBlueprint* Blueprint,
        const FString& EventName,
        float NodeX,
        float NodeY);

    /**
     * Search all loaded UClasses for functions matching the given name (case-insensitive).
     * Returns an array of "ClassName:FunctionName" paths suitable for AddFunctionCallNode.
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static TArray<FString> FindFunctionsByName(const FString& FunctionName);

    /**
     * Add a special (non-function-call) node to a graph.
     * NodeType: "Branch", "Sequence", "ForLoop", "DoOnce", "FlipFlop", "Gate"
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static UEdGraphNode* AddSpecialNode(
        UEdGraph* Graph,
        const FString& NodeType,
        float NodeX,
        float NodeY);

    /**
     * Add a variable getter node (K2Node_VariableGet) for a Blueprint member variable.
     * VariableName must match a variable defined on the Blueprint (same case).
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static UEdGraphNode* AddVariableGetNode(
        UEdGraph* Graph,
        UBlueprint* Blueprint,
        const FString& VariableName,
        float NodeX,
        float NodeY);

    /**
     * Add a variable setter node (K2Node_VariableSet) for a Blueprint member variable.
     */
    UFUNCTION(BlueprintCallable, Category="UnrealAI|Graph")
    static UEdGraphNode* AddVariableSetNode(
        UEdGraph* Graph,
        UBlueprint* Blueprint,
        const FString& VariableName,
        float NodeX,
        float NodeY);
};
