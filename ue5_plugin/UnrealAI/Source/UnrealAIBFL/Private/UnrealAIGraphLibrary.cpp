#include "UnrealAIGraphLibrary.h"

#include "EdGraph/EdGraph.h"
#include "K2Node_Event.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_ExecutionSequence.h"
#include "K2Node_MacroInstance.h"
#include "K2Node_Self.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraphSchema.h"
#include "Engine/Blueprint.h"
#include "K2Node_CallFunction.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "UObject/UObjectGlobals.h"

// Behavior Tree
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/BTNode.h"
#include "BehaviorTree/BTTaskNode.h"
#include "BehaviorTree/Composites/BTComposite_Sequence.h"
#include "BehaviorTree/Composites/BTComposite_Selector.h"
#include "BehaviorTree/Composites/BTComposite_SimpleParallel.h"
#include "BehaviorTreeGraph.h"
#include "BehaviorTreeGraphNode.h"
#include "BehaviorTreeGraphNode_Composite.h"
#include "BehaviorTreeGraphNode_Task.h"
#include "BehaviorTreeGraphNode_Root.h"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

static UFunction* FindFunctionByPath(const FString& FunctionPath)
{
    // Format 1: "ClassName:FunctionName" or "/Script/Engine.ClassName:FunctionName"
    FString ClassPath, FuncName;
    if (FunctionPath.Split(TEXT(":"), &ClassPath, &FuncName))
    {
        UClass* Class = FindObject<UClass>(nullptr, *ClassPath, true);
        if (!Class) Class = LoadObject<UClass>(nullptr, *ClassPath);
        if (Class) return Class->FindFunctionByName(*FuncName);
        return nullptr;
    }

    // Format 2: bare function name — search all loaded Blueprint Function Libraries first,
    // then all loaded UClasses (finds the first match).
    FName FuncFName(*FunctionPath);

    // Prioritise BlueprintFunctionLibrary subclasses (most common case for node calls)
    for (TObjectIterator<UClass> It; It; ++It)
    {
        if (!It->IsChildOf(UBlueprintFunctionLibrary::StaticClass())) continue;
        if (UFunction* Func = It->FindFunctionByName(FuncFName, EIncludeSuperFlag::ExcludeSuper))
        {
            return Func;
        }
    }
    // Fall back to any loaded class
    for (TObjectIterator<UClass> It; It; ++It)
    {
        if (It->IsChildOf(UBlueprintFunctionLibrary::StaticClass())) continue;
        if (UFunction* Func = It->FindFunctionByName(FuncFName, EIncludeSuperFlag::ExcludeSuper))
        {
            return Func;
        }
    }
    return nullptr;
}

// ---------------------------------------------------------------------------
// AddFunctionCallNode
// ---------------------------------------------------------------------------

UEdGraphNode* UUnrealAIGraphLibrary::AddFunctionCallNode(
    UEdGraph* Graph,
    const FString& FunctionPath,
    float NodeX,
    float NodeY)
{
    if (!Graph) return nullptr;

    UFunction* Function = FindFunctionByPath(FunctionPath);
    if (!Function)
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: AddFunctionCallNode — function not found: %s"), *FunctionPath);
        return nullptr;
    }

    UK2Node_CallFunction* NewNode = NewObject<UK2Node_CallFunction>(Graph);
    NewNode->SetFromFunction(Function);
    NewNode->NodePosX = static_cast<int32>(NodeX);
    NewNode->NodePosY = static_cast<int32>(NodeY);

    Graph->AddNode(NewNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
    NewNode->PostPlacedNewNode();
    NewNode->AllocateDefaultPins();

    return NewNode;
}

// ---------------------------------------------------------------------------
// ConnectGraphPins
// ---------------------------------------------------------------------------

bool UUnrealAIGraphLibrary::ConnectGraphPins(
    UEdGraph* Graph,
    const FString& FromNodeName,
    const FString& FromPinName,
    const FString& ToNodeName,
    const FString& ToPinName)
{
    if (!Graph) return false;

    UEdGraphNode* FromNode = nullptr;
    UEdGraphNode* ToNode   = nullptr;

    for (UEdGraphNode* Node : Graph->Nodes)
    {
        if (!Node) continue;
        if (Node->GetName() == FromNodeName) FromNode = Node;
        if (Node->GetName() == ToNodeName)   ToNode   = Node;
    }

    if (!FromNode || !ToNode)
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: ConnectGraphPins — node not found (from=%s to=%s)"),
            *FromNodeName, *ToNodeName);
        return false;
    }

    UEdGraphPin* SourcePin = FromNode->FindPin(*FromPinName, EGPD_Output);
    UEdGraphPin* DestPin   = ToNode->FindPin(*ToPinName,   EGPD_Input);

    if (!SourcePin || !DestPin)
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: ConnectGraphPins — pin not found (from_pin=%s to_pin=%s)"),
            *FromPinName, *ToPinName);
        return false;
    }

    const UEdGraphSchema* Schema = Graph->GetSchema();
    if (!Schema) return false;

    FPinConnectionResponse Response = Schema->CanCreateConnection(SourcePin, DestPin);
    if (Response.Response == CONNECT_RESPONSE_DISALLOW) return false;

    return Schema->TryCreateConnection(SourcePin, DestPin);
}

// ---------------------------------------------------------------------------
// SetVariableDefaultValue
// ---------------------------------------------------------------------------

bool UUnrealAIGraphLibrary::SetVariableDefaultValue(
    UBlueprint* Blueprint,
    const FString& VariableName,
    const FString& DefaultValue)
{
    if (!Blueprint) return false;

    FName VarFName(*VariableName);
    for (FBPVariableDescription& Var : Blueprint->NewVariables)
    {
        if (Var.VarName == VarFName)
        {
            Var.DefaultValue = DefaultValue;
            FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
            return true;
        }
    }

    UE_LOG(LogTemp, Warning, TEXT("UnrealAI: SetVariableDefaultValue — variable not found: %s"), *VariableName);
    return false;
}

// ---------------------------------------------------------------------------
// GetGraphNodes
// ---------------------------------------------------------------------------

TArray<FUnrealAINodeInfo> UUnrealAIGraphLibrary::GetGraphNodes(UEdGraph* Graph)
{
    TArray<FUnrealAINodeInfo> Result;
    if (!Graph) return Result;

    for (UEdGraphNode* Node : Graph->Nodes)
    {
        if (!Node) continue;

        FUnrealAINodeInfo Info;
        Info.NodeName  = Node->GetName();
        Info.NodeClass = Node->GetClass()->GetName();

        for (UEdGraphPin* Pin : Node->Pins)
        {
            if (!Pin) continue;
            if (Pin->Direction == EGPD_Input)
                Info.InputPins.Add(Pin->GetName());
            else
                Info.OutputPins.Add(Pin->GetName());
        }

        Result.Add(MoveTemp(Info));
    }

    return Result;
}

// ---------------------------------------------------------------------------
// AddSpecialNode
// ---------------------------------------------------------------------------

UEdGraphNode* UUnrealAIGraphLibrary::AddSpecialNode(
    UEdGraph* Graph,
    const FString& NodeType,
    float NodeX,
    float NodeY)
{
    if (!Graph) return nullptr;

    UEdGraphNode* NewNode = nullptr;

    if (NodeType.Equals(TEXT("Self"), ESearchCase::IgnoreCase))
    {
        UK2Node_Self* Node = NewObject<UK2Node_Self>(Graph);
        NewNode = Node;
    }
    else if (NodeType.Equals(TEXT("Branch"), ESearchCase::IgnoreCase))
    {
        UK2Node_IfThenElse* Node = NewObject<UK2Node_IfThenElse>(Graph);
        NewNode = Node;
    }
    else if (NodeType.Equals(TEXT("Sequence"), ESearchCase::IgnoreCase))
    {
        UK2Node_ExecutionSequence* Node = NewObject<UK2Node_ExecutionSequence>(Graph);
        NewNode = Node;
    }
    else if (NodeType.Equals(TEXT("ForLoop"), ESearchCase::IgnoreCase)   ||
             NodeType.Equals(TEXT("DoOnce"), ESearchCase::IgnoreCase)    ||
             NodeType.Equals(TEXT("FlipFlop"), ESearchCase::IgnoreCase)  ||
             NodeType.Equals(TEXT("Gate"), ESearchCase::IgnoreCase))
    {
        // These are Blueprint macros from StandardMacros library
        const FString MacroPath = FString::Printf(
            TEXT("/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:%s"), *NodeType);
        UEdGraph* MacroGraph = LoadObject<UEdGraph>(nullptr, *MacroPath);
        if (!MacroGraph)
        {
            UE_LOG(LogTemp, Warning, TEXT("UnrealAI: AddSpecialNode — could not load macro: %s"), *MacroPath);
            return nullptr;
        }
        UK2Node_MacroInstance* Node = NewObject<UK2Node_MacroInstance>(Graph);
        Node->SetMacroGraph(MacroGraph);
        NewNode = Node;
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: AddSpecialNode — unknown node type: %s"), *NodeType);
        return nullptr;
    }

    if (NewNode)
    {
        NewNode->NodePosX = static_cast<int32>(NodeX);
        NewNode->NodePosY = static_cast<int32>(NodeY);
        Graph->AddNode(NewNode, false, false);
        NewNode->PostPlacedNewNode();
        NewNode->AllocateDefaultPins();
    }

    return NewNode;
}

// ---------------------------------------------------------------------------
// AddVariableGetNode / AddVariableSetNode
// ---------------------------------------------------------------------------

static UEdGraphNode* AddVariableNode(UEdGraph* Graph, UBlueprint* Blueprint,
    const FString& VariableName, float NodeX, float NodeY, bool bSetter)
{
    if (!Graph || !Blueprint) return nullptr;

    FName VarFName(*VariableName);

    // Find the property on the generated class
    UClass* GenClass = Blueprint->GeneratedClass;
    if (!GenClass)
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: AddVariableNode — Blueprint has no GeneratedClass"));
        return nullptr;
    }

    // Check NewVariables first (covers uncompiled blueprints)
    bool bFound = false;
    for (const FBPVariableDescription& Var : Blueprint->NewVariables)
    {
        if (Var.VarName == VarFName) { bFound = true; break; }
    }
    // Also accept properties already compiled onto GeneratedClass
    if (!bFound && GenClass->FindPropertyByName(VarFName))
    {
        bFound = true;
    }
    if (!bFound)
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: AddVariableNode — variable not found: %s"), *VariableName);
        return nullptr;
    }

    // SetDirect explicitly points the reference at the Blueprint's generated class,
    // which is what UE needs to resolve user-defined Blueprint variables.
    FMemberReference VarRef;
    VarRef.SetDirect(VarFName, FGuid(), GenClass, /*bIsConsideredSelfContext=*/false);

    UEdGraphNode* NewNode = nullptr;
    if (bSetter)
    {
        UK2Node_VariableSet* Node = NewObject<UK2Node_VariableSet>(Graph);
        Node->VariableReference = VarRef;
        NewNode = Node;
    }
    else
    {
        UK2Node_VariableGet* Node = NewObject<UK2Node_VariableGet>(Graph);
        Node->VariableReference = VarRef;
        NewNode = Node;
    }

    NewNode->NodePosX = static_cast<int32>(NodeX);
    NewNode->NodePosY = static_cast<int32>(NodeY);
    Graph->AddNode(NewNode, false, false);
    NewNode->PostPlacedNewNode();
    NewNode->AllocateDefaultPins();

    return NewNode;
}

UEdGraphNode* UUnrealAIGraphLibrary::AddVariableGetNode(
    UEdGraph* Graph, UBlueprint* Blueprint,
    const FString& VariableName, float NodeX, float NodeY)
{
    return AddVariableNode(Graph, Blueprint, VariableName, NodeX, NodeY, false);
}

UEdGraphNode* UUnrealAIGraphLibrary::AddVariableSetNode(
    UEdGraph* Graph, UBlueprint* Blueprint,
    const FString& VariableName, float NodeX, float NodeY)
{
    return AddVariableNode(Graph, Blueprint, VariableName, NodeX, NodeY, true);
}

// ---------------------------------------------------------------------------
// FindFunctionsByName
// ---------------------------------------------------------------------------

TArray<FString> UUnrealAIGraphLibrary::FindFunctionsByName(const FString& FunctionName)
{
    TArray<FString> Results;
    FName FuncFName(*FunctionName);

    for (TObjectIterator<UClass> It; It; ++It)
    {
        UClass* Class = *It;
        UFunction* Func = Class->FindFunctionByName(FuncFName, EIncludeSuperFlag::ExcludeSuper);
        if (!Func) continue;

        // Only include callable functions (skip internal/editor-only noise)
        if (!Func->HasAnyFunctionFlags(FUNC_BlueprintCallable | FUNC_BlueprintPure)) continue;

        FString Path = FString::Printf(TEXT("%s:%s"),
            *Class->GetPathName(), *FunctionName);
        Results.Add(Path);
    }

    return Results;
}

// ---------------------------------------------------------------------------
// GetEventNodeFunctionName / AddOrFindEventNode
// ---------------------------------------------------------------------------

FString UUnrealAIGraphLibrary::GetEventNodeFunctionName(UEdGraph* Graph, const FString& NodeName)
{
    if (!Graph) return FString();
    for (UEdGraphNode* Node : Graph->Nodes)
    {
        if (!Node || Node->GetName() != NodeName) continue;
        if (UK2Node_Event* EventNode = Cast<UK2Node_Event>(Node))
        {
            return EventNode->EventReference.GetMemberName().ToString();
        }
    }
    return FString();
}

UEdGraphNode* UUnrealAIGraphLibrary::AddOrFindEventNode(
    UEdGraph* Graph,
    UBlueprint* Blueprint,
    const FString& EventName,
    float NodeX,
    float NodeY)
{
    if (!Graph || !Blueprint) return nullptr;

    // Map common display names to the actual Blueprint-overridable function names
    static const TMap<FString, FString> EventNameMap =
    {
        { TEXT("Tick"),               TEXT("ReceiveTick") },
        { TEXT("BeginPlay"),          TEXT("ReceiveBeginPlay") },
        { TEXT("EndPlay"),            TEXT("ReceiveEndPlay") },
        { TEXT("ActorBeginOverlap"),  TEXT("ReceiveActorBeginOverlap") },
        { TEXT("ActorEndOverlap"),    TEXT("ReceiveActorEndOverlap") },
        { TEXT("Hit"),                TEXT("ReceiveHit") },
        { TEXT("Destroyed"),          TEXT("ReceiveDestroyed") },
        { TEXT("TakeAnyDamage"),      TEXT("ReceiveAnyDamage") },
    };

    const FString* MappedName = EventNameMap.Find(EventName);
    FName FuncFName(MappedName ? **MappedName : *EventName);

    // Check if node already exists in graph
    for (UEdGraphNode* Node : Graph->Nodes)
    {
        if (UK2Node_Event* EventNode = Cast<UK2Node_Event>(Node))
        {
            if (EventNode->EventReference.GetMemberName() == FuncFName)
            {
                return EventNode;
            }
        }
    }

    // Find the UFunction in the Blueprint's class hierarchy
    UFunction* EventFunc = nullptr;
    UClass* SearchClass = Blueprint->ParentClass;
    while (SearchClass && !EventFunc)
    {
        EventFunc = SearchClass->FindFunctionByName(FuncFName, EIncludeSuperFlag::ExcludeSuper);
        SearchClass = SearchClass->GetSuperClass();
    }

    if (!EventFunc)
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: AddOrFindEventNode — function not found: %s"), *EventName);
        return nullptr;
    }

    UK2Node_Event* NewNode = NewObject<UK2Node_Event>(Graph);
    NewNode->EventReference.SetFromField<UFunction>(EventFunc, false);
    NewNode->bOverrideFunction = true;
    NewNode->NodePosX = static_cast<int32>(NodeX);
    NewNode->NodePosY = static_cast<int32>(NodeY);

    Graph->AddNode(NewNode, false, false);
    NewNode->PostPlacedNewNode();
    NewNode->AllocateDefaultPins();

    return NewNode;
}

// ---------------------------------------------------------------------------
// GetVariableNames
// ---------------------------------------------------------------------------

TArray<FString> UUnrealAIGraphLibrary::GetVariableNames(UBlueprint* Blueprint)
{
    TArray<FString> Names;
    if (!Blueprint) return Names;
    for (const FBPVariableDescription& Var : Blueprint->NewVariables)
    {
        Names.Add(Var.VarName.ToString());
    }
    return Names;
}

// ---------------------------------------------------------------------------
// Behavior Tree helpers
// ---------------------------------------------------------------------------

static UEdGraph* GetBTGraph(UBehaviorTree* BT)
{
    if (!BT) return nullptr;
    return Cast<UEdGraph>(BT->BTGraph);
}

// ---------------------------------------------------------------------------
// AddBTCompositeNode
// ---------------------------------------------------------------------------

UEdGraphNode* UUnrealAIGraphLibrary::AddBTCompositeNode(
    UBehaviorTree* BT,
    const FString& CompositeType,
    float NodeX,
    float NodeY)
{
    UEdGraph* BTGraph = GetBTGraph(BT);
    if (!BTGraph) return nullptr;

    UBTCompositeNode* CompositeInstance = nullptr;
    if (CompositeType.Equals(TEXT("Sequence"), ESearchCase::IgnoreCase))
        CompositeInstance = NewObject<UBTComposite_Sequence>(BT);
    else if (CompositeType.Equals(TEXT("Selector"), ESearchCase::IgnoreCase))
        CompositeInstance = NewObject<UBTComposite_Selector>(BT);
    else if (CompositeType.Equals(TEXT("SimpleParallel"), ESearchCase::IgnoreCase))
        CompositeInstance = NewObject<UBTComposite_SimpleParallel>(BT);
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: AddBTCompositeNode — unknown type: %s"), *CompositeType);
        return nullptr;
    }

    UBehaviorTreeGraphNode_Composite* GraphNode =
        NewObject<UBehaviorTreeGraphNode_Composite>(BTGraph);
    GraphNode->NodeInstance = CompositeInstance;
    GraphNode->NodePosX = static_cast<int32>(NodeX);
    GraphNode->NodePosY = static_cast<int32>(NodeY);

    BTGraph->AddNode(GraphNode, /*bUserAction=*/false, /*bSelectNewNode=*/false);
    GraphNode->PostPlacedNewNode();
    GraphNode->AllocateDefaultPins();

    return GraphNode;
}

// ---------------------------------------------------------------------------
// AddBTTaskNode
// ---------------------------------------------------------------------------

UEdGraphNode* UUnrealAIGraphLibrary::AddBTTaskNode(
    UBehaviorTree* BT,
    const FString& TaskClass,
    float NodeX,
    float NodeY)
{
    UEdGraph* BTGraph = GetBTGraph(BT);
    if (!BTGraph) return nullptr;

    // Resolve class — short names first, then direct path lookup
    static const TMap<FString, FString> BuiltinTasks =
    {
        { TEXT("Wait"),                    TEXT("/Script/AIModule.BTTask_Wait") },
        { TEXT("MoveTo"),                  TEXT("/Script/AIModule.BTTask_MoveTo") },
        { TEXT("MoveDirectlyToward"),      TEXT("/Script/AIModule.BTTask_MoveDirectlyToward") },
        { TEXT("RunBehavior"),             TEXT("/Script/AIModule.BTTask_RunBehavior") },
        { TEXT("RunEQSQuery"),             TEXT("/Script/AIModule.BTTask_RunEQSQuery") },
        { TEXT("RotateToFaceBBEntry"),     TEXT("/Script/AIModule.BTTask_RotateToFaceBBEntry") },
        { TEXT("SetTagCooldown"),          TEXT("/Script/AIModule.BTTask_SetTagCooldown") },
        { TEXT("PlayAnimation"),           TEXT("/Script/AIModule.BTTask_PlayAnimation") },
        { TEXT("PlaySound"),               TEXT("/Script/AIModule.BTTask_PlaySound") },
        { TEXT("BlueprintBase"),           TEXT("/Script/AIModule.BTTask_BlueprintBase") },
    };

    UClass* TaskUClass = nullptr;
    if (const FString* BuiltinPath = BuiltinTasks.Find(TaskClass))
    {
        TaskUClass = FindObject<UClass>(nullptr, **BuiltinPath, true);
        if (!TaskUClass) TaskUClass = LoadObject<UClass>(nullptr, **BuiltinPath);
    }
    if (!TaskUClass)
    {
        TaskUClass = FindObject<UClass>(nullptr, *TaskClass, true);
        if (!TaskUClass) TaskUClass = LoadObject<UClass>(nullptr, *TaskClass);
    }
    if (!TaskUClass || !TaskUClass->IsChildOf(UBTTaskNode::StaticClass()))
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealAI: AddBTTaskNode — task class not found: %s"), *TaskClass);
        return nullptr;
    }

    UBTTaskNode* TaskInstance = NewObject<UBTTaskNode>(BT, TaskUClass);

    UBehaviorTreeGraphNode_Task* GraphNode =
        NewObject<UBehaviorTreeGraphNode_Task>(BTGraph);
    GraphNode->NodeInstance = TaskInstance;
    GraphNode->NodePosX = static_cast<int32>(NodeX);
    GraphNode->NodePosY = static_cast<int32>(NodeY);

    BTGraph->AddNode(GraphNode, false, false);
    GraphNode->PostPlacedNewNode();
    GraphNode->AllocateDefaultPins();

    return GraphNode;
}

// ---------------------------------------------------------------------------
// DeleteBTNode
// ---------------------------------------------------------------------------

bool UUnrealAIGraphLibrary::DeleteBTNode(
    UBehaviorTree* BT,
    const FString& NodeName)
{
    UEdGraph* BTGraph = GetBTGraph(BT);
    if (!BTGraph) return false;

    for (int32 i = BTGraph->Nodes.Num() - 1; i >= 0; --i)
    {
        UEdGraphNode* Node = BTGraph->Nodes[i];
        if (!Node || Node->GetName() != NodeName) continue;

        if (Node->IsA<UBehaviorTreeGraphNode_Root>())
        {
            UE_LOG(LogTemp, Warning, TEXT("UnrealAI: DeleteBTNode — cannot delete root node"));
            return false;
        }

        Node->BreakAllNodeLinks();
        BTGraph->RemoveNode(Node);
        return true;
    }

    UE_LOG(LogTemp, Warning, TEXT("UnrealAI: DeleteBTNode — node not found: %s"), *NodeName);
    return false;
}

// ---------------------------------------------------------------------------
// ConnectBTNodes
// ---------------------------------------------------------------------------

bool UUnrealAIGraphLibrary::ConnectBTNodes(
    UBehaviorTree* BT,
    const FString& ParentNodeName,
    const FString& ChildNodeName)
{
    UEdGraph* BTGraph = GetBTGraph(BT);
    if (!BTGraph) return false;

    UEdGraphNode* ParentNode = nullptr;
    UEdGraphNode* ChildNode  = nullptr;
    for (UEdGraphNode* Node : BTGraph->Nodes)
    {
        if (!Node) continue;
        if (Node->GetName() == ParentNodeName) ParentNode = Node;
        if (Node->GetName() == ChildNodeName)  ChildNode  = Node;
    }
    if (!ParentNode || !ChildNode) return false;

    UEdGraphPin* OutPin = nullptr;
    for (UEdGraphPin* Pin : ParentNode->Pins)
    {
        if (Pin && Pin->Direction == EGPD_Output) { OutPin = Pin; break; }
    }
    UEdGraphPin* InPin = nullptr;
    for (UEdGraphPin* Pin : ChildNode->Pins)
    {
        if (Pin && Pin->Direction == EGPD_Input) { InPin = Pin; break; }
    }
    if (!OutPin || !InPin) return false;

    const UEdGraphSchema* Schema = BTGraph->GetSchema();
    if (!Schema) return false;

    FPinConnectionResponse Response = Schema->CanCreateConnection(OutPin, InPin);
    if (Response.Response == CONNECT_RESPONSE_DISALLOW) return false;

    return Schema->TryCreateConnection(OutPin, InPin);
}

// ---------------------------------------------------------------------------
// DisconnectBTNodes
// ---------------------------------------------------------------------------

bool UUnrealAIGraphLibrary::DisconnectBTNodes(
    UBehaviorTree* BT,
    const FString& ParentNodeName,
    const FString& ChildNodeName)
{
    UEdGraph* BTGraph = GetBTGraph(BT);
    if (!BTGraph) return false;

    UEdGraphNode* ParentNode = nullptr;
    UEdGraphNode* ChildNode  = nullptr;
    for (UEdGraphNode* Node : BTGraph->Nodes)
    {
        if (!Node) continue;
        if (Node->GetName() == ParentNodeName) ParentNode = Node;
        if (Node->GetName() == ChildNodeName)  ChildNode  = Node;
    }
    if (!ParentNode || !ChildNode) return false;

    UEdGraphPin* OutPin = nullptr;
    for (UEdGraphPin* Pin : ParentNode->Pins)
    {
        if (Pin && Pin->Direction == EGPD_Output) { OutPin = Pin; break; }
    }
    UEdGraphPin* InPin = nullptr;
    for (UEdGraphPin* Pin : ChildNode->Pins)
    {
        if (Pin && Pin->Direction == EGPD_Input) { InPin = Pin; break; }
    }
    if (!OutPin || !InPin) return false;

    if (!OutPin->LinkedTo.Contains(InPin)) return false;

    OutPin->BreakLinkTo(InPin);
    return true;
}

// ---------------------------------------------------------------------------
// GetBTNodes
// ---------------------------------------------------------------------------

TArray<FUnrealAINodeInfo> UUnrealAIGraphLibrary::GetBTNodes(UBehaviorTree* BT)
{
    UEdGraph* BTGraph = GetBTGraph(BT);
    if (!BTGraph) return {};
    return GetGraphNodes(BTGraph);
}
