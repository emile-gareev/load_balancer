"""
This code implements a simple load balancer API in Python.
The balancer can register up to 10 servers without duplicates and supports two load balancing strategies:
- round robin
- random.

The asyncio library is used for implementation, which allows working with asynchronous operations.

The code follows the SOLID principles and uses the Strategy design pattern.

*** Python 3.10+

Optional[str] can be shortened to str | None
"""

import asyncio
import random
from abc import ABC, abstractmethod
# from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Set


class LoadBalancingStrategy(ABC):
    """
    (interface): Defines the select_server method that all load balancing strategies must implement.
    Allows new strategies to be easily added without changing the core code.
    """
    @abstractmethod
    def select_server(self, servers: List[str]) -> Optional[str]:
        ...


class RoundRobinStrategy(LoadBalancingStrategy):
    """
    Implements a round-robin strategy, selecting servers in turn (with sorting).
    Complies with the Single Responsibility Principle (SRP), since it is responsible only for its own strategy.
    """
    def __init__(self):
        self.index = 0

    def select_server(self, servers: List[str]) -> Optional[str]:
        if not servers:
            return None
        servers = sorted(servers)  # Sorting servers
        server = servers[self.index]
        self.index = (self.index + 1) % len(servers)
        return server

    def reset(self):
        """Resets the index to 0."""
        self.index = 0


class RandomStrategy(LoadBalancingStrategy):
    """
    Selects a server randomly from a list.
    Complies with the Single Responsibility Principle (SRP), as it is responsible only for its own strategy.
    """
    def select_server(self, servers: List[str]) -> Optional[str]:
        if not servers:
            return None
        return random.choice(servers)


class LoadBalancer:
    """
    The main class that manages server registration and strategy selection.
    It provides thread safety via asyncio.Lock.
    """
    def __init__(self, max_instances: int = 10):
        self.servers: Set[str] = set()
        self.max_instances: int = max_instances
        self.strategy: LoadBalancingStrategy = RoundRobinStrategy()
        self.lock = asyncio.Lock()
        # self.executor = ThreadPoolExecutor(max_workers=10)

    async def register_server(self, server: str) -> bool:
        """
        Method for registering servers.
        Checks that the number of servers does not exceed the maximum value
        and that the server has not been registered previously.
        """
        try:
            async with self.lock:
                if len(self.servers) >= self.max_instances:
                    print("Maximum number of servers reached.")
                    return False
                if server in self.servers:
                    print(f"Server {server} is already registered.")
                    return False
                self.servers.add(server)
                print(f"Server {server} has been registered successfully.")
                return True
        except Exception as e:
            print(f"Error registering server: {e}")
            return False

    async def remove_server(self, server: str) -> bool:
        """Method for deleting servers."""
        async with self.lock:
            if server in self.servers:
                self.servers.remove(server)
                print(f"Server {server} has been successfully removed.")
                return True
            print(f"Server {server} not found.")
            return False

    def set_strategy(self, strategy: LoadBalancingStrategy):
        """Sets the balancer strategy."""
        if not isinstance(strategy, LoadBalancingStrategy):
            raise ValueError("The strategy must be an instance of LoadBalancingStrategy")
        self.strategy = strategy

    async def get_server(self) -> Optional[str]:
        """Returns the server according to the selected strategy."""
        async with self.lock:
            if not self.servers:
                print("There are no registered servers.")
                return None
            return self.strategy.select_server(list(self.servers))
            # return await asyncio.get_event_loop().run_in_executor(
            #     self.executor,
            #     self.strategy.select_server, list(self.servers)
            # )


class Account:
    """Represents an account with an ID and balance."""
    def __init__(self, account_id: str, balance: float):
        self.account_id = account_id
        self.balance = balance
        self.lock = asyncio.Lock()  # Locking to ensure thread safety

    async def transfer(self, amount: float, target_account: 'Account'):
        """Allows you to transfer money between accounts using locking to ensure thread safety."""

        # First, we block both accounts to avoid a race condition.
        async with self.lock, target_account.lock:
            if amount <= 0:
                raise ValueError("The transfer amount must be positive.")
            if self.balance < amount:
                raise ValueError("Insufficient funds for transfer.")

            self.balance -= amount
            target_account.balance += amount
            print(f"Transfer by {amount} {self.account_id} to {target_account.account_id}.")


async def main():
    """Example of use."""
    load_balancer = LoadBalancer()

    await load_balancer.register_server("192.168.1.1")
    await load_balancer.register_server("192.168.1.2")
    await load_balancer.register_server("192.168.1.3")

    load_balancer.set_strategy(RoundRobinStrategy())

    for _ in range(5):
        server = await load_balancer.get_server()
        print(f"Selected server: {server}")

    # Creating accounts
    account1 = Account("Account1", 100.0)
    account2 = Account("Account2", 50.0)

    # Parallel transfers
    async def perform_transfer():
        try:
            await account1.transfer(30.0, account2)
        except ValueError as e:
            print(e)

    # Launching multiple transfers
    await asyncio.gather(perform_transfer(), perform_transfer())

    # Check balance
    print(f"{account1.account_id} balance: {account1.balance}")
    print(f"{account2.account_id} balance: {account2.balance}")


if __name__ == "__main__":
    asyncio.run(main())
