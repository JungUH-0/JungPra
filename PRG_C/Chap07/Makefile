CC = c++
TARGET = application
SOURCES = time.cpp app.cpp
OBJECTS = $(SOURCES:.cpp=.o)
 
$(TARGET): $(OBJECTS)
	$(CC) -o $@ $^

%.o: %.cpp
	$(CC) -c $<
 
clean:
	rm -f $(OBJECTS) $(TARGET)
 
.PHONY: clean