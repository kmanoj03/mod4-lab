# Module 4: Architecture & Service Boundaries

A small online store split into independent services. Order Service and Inventory Service are implemented in Python (Flask) and run as separate processes. Notification Service is part of the design only.

## Architecture Diagram

```mermaid
flowchart LR
    Client([Client / curl])

    subgraph OS[Order Service :5001]
        OAPI[REST API]
        ODB[(Orders<br/>in-memory)]
    end

    subgraph IS[Inventory Service :5002]
        IAPI[REST API]
        IDB[(Stock levels<br/>in-memory)]
    end

    subgraph NS[Notification Service - design only]
        NWORKER[Event consumer]
        NDB[(Notification log)]
    end

    Bus{{Message broker}}

    Client -- "POST /orders (Command)" --> OAPI
    OAPI -- "GET /inventory/:item_id (Query, sync HTTP)" --> IAPI
    IAPI -- "available / unavailable" --> OAPI
    OAPI --- ODB
    IAPI --- IDB
    OAPI -. "OrderCreated (Event, async)" .-> Bus
    Bus -. "OrderCreated" .-> NWORKER
    NWORKER --- NDB
```

Solid lines are synchronous HTTP calls (implemented). Dashed lines are asynchronous events through a message broker (design only).

## Components

| Service | Responsibility | Data it owns |
|---|---|---|
| **Order Service** | Accepts new orders, checks item availability with Inventory, creates and tracks orders, and publishes an `OrderCreated` event. | Orders: order ID, item ID, quantity, status. |
| **Inventory Service** | Tracks item availability and answers whether a requested quantity of an item is in stock. | Items and their stock levels. |
| **Notification Service** | Listens for `OrderCreated` events and notifies the user. | Notification records (who was notified, when, and the delivery status). |

Each service is the only one that reads or writes its own data. Other services get that data only through the owning service's API or events. For example, Order Service never reads stock levels directly; it asks Inventory Service.

## Why These Service Boundaries

- **Each service maps to one business capability.** Orders, stock, and notifications change for different reasons and can be owned and deployed separately.
- **Data has a single owner.** Stock levels live only in Inventory, so there is one source of truth and no shared database coupling the services.
- **Coupling matches the need.** Order *must* know availability before creating an order, so that call is synchronous. Notifying the user does not need to block order creation, so Notification is decoupled through an event. A slow or failed Notification Service cannot break ordering.
- **Failures are isolated.** If Inventory goes down, Order Service stays up and returns a clear error instead of crashing (see the failure test below).

## Command, Query, and Event

| Interaction | Type | Why |
|---|---|---|
| Check whether an item is available | **Query** | It asks Inventory Service for information and changes no state. Calling it twice gives the same answer. |
| Create an order | **Command** | It is a request to perform an action that changes state (a new order is stored). It is directed at one service, which can accept or reject it. |
| Order was created | **Event** | It announces a fact that already happened, named in the past tense. Order Service publishes it without knowing or waiting for who consumes it (e.g. Notification Service). |
